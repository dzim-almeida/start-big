/**
 * @fileoverview A produção de uma OS: a leitura e as ações (Spec 12B D11, §7.3).
 *
 * - A query só roda com a aba ABERTA (os outros segmentos nunca chamam
 *   `/marcenaria/...`) e recarrega a cada `REFETCH_REALTIME` enquanto nenhum
 *   modal da aba estiver aberto e nada estiver sendo gravado: dois marceneiros
 *   marcando em sequência veem o trabalho um do outro.
 * - Marcação OTIMISTA (D11): a etapa muda na tela na hora do clique; a
 *   resposta do servidor é a verdade e substitui tudo; se falhar, a tela volta
 *   a como estava e um toast avisa.
 * - Toda escrita pode trazer a `sugestao_status` (12A D16): ela fica em
 *   `sugestao` para a aba perguntar se move a OS (D12).
 */
import { computed, ref, type Ref } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';

import { REFETCH_REALTIME } from '@/core/config/queryIntervals';
import { useToast } from '@/shared/composables/useToast';
import { mensagemDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';
import { CHAVE_PRODUCAO } from '@/modules/marcenaria/terceirizados/composables/useTerceirizadosDaOS';
import type { SugestaoStatus } from '@/modules/marcenaria/terceirizados/schemas/terceirizado.schema';

import type { ProducaoDaOS, StatusEtapa } from '../schemas/producao.schema';
import * as servico from '../services/producao.service';
import { marcarLocalmente } from '../utils/producao';

/** A chave do cache da produção de uma OS (dentro do prefixo que a 11B invalida). */
export const chaveProducao = (numeroOs: string) => [...CHAVE_PRODUCAO, 'os', numeroOs] as const;
/** A chave do quadro da fábrica (aba "Produção" em Serviços). */
export const CHAVE_QUADRO = [...CHAVE_PRODUCAO, 'quadro'] as const;

export function useProducaoDaOS(numeroOs: Ref<string>, ativo: Ref<boolean>, pausado: Ref<boolean>) {
  const queryClient = useQueryClient();
  const toast = useToast();
  /** Quantas gravações estão no servidor agora (cliques rápidos se sobrepõem). */
  const emVoo = ref(0);
  const gravando = computed(() => emVoo.value > 0);

  const consulta = useQuery({
    queryKey: computed(() => chaveProducao(numeroOs.value)),
    queryFn: () => servico.getProducao(numeroOs.value),
    enabled: computed(() => ativo.value && !!numeroOs.value),
    // Função: o TanStack pergunta de novo a cada ciclo. Com modal aberto ou
    // gravação no ar, não recarrega (a leitura velha desfaria a marcação na tela).
    refetchInterval: () => (pausado.value || gravando.value ? false : REFETCH_REALTIME),
    retry: false,                                    // 404 (OS sem orçamento) não melhora repetindo
  });

  /** A sugestão de status da última escrita (D12). A aba limpa depois de perguntar. */
  const sugestao = ref<SugestaoStatus>(null);

  const chave = () => chaveProducao(numeroOs.value);

  /**
   * Roda a escrita. Com `otimista`, a tela muda antes (D11) e volta se falhar.
   * Devolve true quando gravou.
   */
  async function executar(
    acao: () => Promise<ProducaoDaOS>,
    otimista?: (atual: ProducaoDaOS) => ProducaoDaOS,
    erroTitulo = 'Não foi possível gravar.',
  ): Promise<boolean> {
    // Uma leitura em andamento chegaria depois e desfaria a marcação na tela.
    await queryClient.cancelQueries({ queryKey: chave() });
    const anterior = queryClient.getQueryData<ProducaoDaOS>(chave());   // para desfazer se falhar
    if (otimista && anterior) queryClient.setQueryData(chave(), otimista(anterior));
    emVoo.value += 1;
    try {
      const resposta = await acao();
      queryClient.setQueryData(chave(), resposta);                       // a resposta é a verdade
      void queryClient.invalidateQueries({ queryKey: CHAVE_QUADRO });    // o quadro fica velho
      if (resposta.sugestao_status) sugestao.value = resposta.sugestao_status;
      return true;
    } catch (erro) {
      if (anterior) queryClient.setQueryData(chave(), anterior);         // volta como estava
      toast.error(erroTitulo, mensagemDoErro(erro));
      // Outra pessoa pode ter mudado a OS (409): recarrega para a tela dizer a verdade.
      void queryClient.invalidateQueries({ queryKey: chave() });
      return false;
    } finally {
      emVoo.value -= 1;
    }
  }

  const os = () => numeroOs.value;
  /** Marcação otimista de várias etapas (com o nome de quem fez, quando se sabe). */
  const marcar = (ids: number[], status: StatusEtapa, responsavel: string | null) =>
    (atual: ProducaoDaOS) => marcarLocalmente(atual, ids, status, responsavel);

  return {
    ...consulta,
    gravando,
    sugestao,
    /** Concluir etapas (um clique, a seleção ou "Concluir em todos"). */
    concluir: (ids: number[], responsavelId: number | null, responsavelNome: string | null) =>
      executar(() => servico.concluir(os(), ids, responsavelId), marcar(ids, 'CONCLUIDA', responsavelNome),
        'Não foi possível marcar a etapa.'),
    iniciar: (ids: number[], responsavelId: number | null, responsavelNome: string | null) =>
      executar(() => servico.iniciar(os(), ids, responsavelId), marcar(ids, 'EM_EXECUCAO', responsavelNome),
        'Não foi possível iniciar a etapa.'),
    reabrir: (id: number) =>
      executar(() => servico.reabrir(os(), id), marcar([id], 'PENDENTE', null), 'Não foi possível reabrir a etapa.'),
    /** Editar e aplicar o padrão mexem na lista: sem otimismo (o modal espera a resposta). */
    editarEtapas: (movelId: number, etapas: { id: number | null; nome: string }[]) =>
      executar(() => servico.editarEtapas(os(), movelId, etapas), undefined, 'Não foi possível salvar as etapas.'),
    aplicarPadrao: (movelId: number) =>
      executar(() => servico.aplicarPadrao(os(), movelId), undefined, 'Não foi possível aplicar as etapas padrão.'),
  };
}
