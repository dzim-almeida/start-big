/**
 * @fileoverview A entrega de uma OS: a leitura e as ações (Spec 13B).
 *
 * - A query só roda com a aba ABERTA (os outros segmentos nunca chamam
 *   `/marcenaria/...`) e recarrega a cada `REFETCH_REALTIME` enquanto nenhum
 *   modal da aba estiver aberto.
 * - Toda ação devolve a aba atualizada (13A): ela entra direto no cache.
 *   Depois, a lista de instalações e o resumo da finalização ficam velhos e
 *   são invalidados.
 * - Erro: toast com a frase da API e a aba relê (outra pessoa pode ter mexido).
 */
import { computed, ref, type Ref } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';

import { REFETCH_REALTIME } from '@/core/config/queryIntervals';
import { useToast } from '@/shared/composables/useToast';
import { mensagemDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';

import type { EntregaDaOS } from '../schemas/entrega.schema';
import * as agenda from '../services/agenda.service';
import * as servico from '../services/entrega.service';

/** O começo de todas as chaves da entrega (aba, resumo e instalações). */
export const CHAVE_ENTREGA = ['marcenaria', 'entrega'] as const;
export const chaveEntregaDaOS = (numeroOs: string) => [...CHAVE_ENTREGA, 'os', numeroOs] as const;
export const chaveResumo = (numeroOs: string) => [...CHAVE_ENTREGA, 'resumo', numeroOs] as const;
export const CHAVE_INSTALACOES = [...CHAVE_ENTREGA, 'instalacoes'] as const;

export function useEntregaDaOS(numeroOs: Ref<string>, ativo: Ref<boolean>, pausado: Ref<boolean>) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const gravando = ref(false);

  const consulta = useQuery({
    queryKey: computed(() => chaveEntregaDaOS(numeroOs.value)),
    queryFn: () => servico.getEntrega(numeroOs.value),
    enabled: computed(() => ativo.value && !!numeroOs.value),
    // Com modal aberto ou gravando, não recarrega (o formulário não pode mudar por baixo).
    refetchInterval: () => (pausado.value || gravando.value ? false : REFETCH_REALTIME),
    retry: false,                                    // 404 (OS sem orçamento) não melhora repetindo
  });

  /** Roda a ação e guarda a resposta. Devolve a aba nova, ou null se não gravou. */
  async function executar(acao: () => Promise<EntregaDaOS>, sucesso?: string): Promise<EntregaDaOS | null> {
    gravando.value = true;
    try {
      const nova = await acao();
      queryClient.setQueryData(chaveEntregaDaOS(numeroOs.value), nova);       // a tela já mostra o novo
      void queryClient.invalidateQueries({ queryKey: CHAVE_INSTALACOES });     // a lista de Serviços
      void queryClient.invalidateQueries({ queryKey: chaveResumo(numeroOs.value) });   // o aviso da finalização
      if (sucesso) toast.success(sucesso);
      return nova;
    } catch (erro) {
      toast.error(mensagemDoErro(erro));
      void queryClient.invalidateQueries({ queryKey: chaveEntregaDaOS(numeroOs.value) });
      return null;
    } finally {
      gravando.value = false;
    }
  }

  const os = () => numeroOs.value;
  return {
    ...consulta,
    gravando,
    executar,
    agendar: (dados: agenda.AgendamentoEnvio) => executar(() => agenda.agendar(os(), dados), 'Instalação agendada.'),
    editarAgendamento: (id: number, dados: agenda.AgendamentoEnvio) =>
      executar(() => agenda.editarAgendamento(os(), id, dados), 'Instalação remarcada.'),
    excluirAgendamento: (id: number) => executar(() => agenda.excluirAgendamento(os(), id), 'Instalação desmarcada.'),
    editarChecklist: (entregaId: number, itens: string[]) =>
      executar(() => servico.editarChecklist(os(), entregaId, itens), 'Checklist salvo.'),
    registrar: (entregaId: number, registro: servico.RegistroEntrega) =>
      executar(() => servico.registrar(os(), entregaId, registro), 'Entrega registrada.'),
    criarPendencia: (entregaId: number, descricao: string) =>
      executar(() => servico.criarPendencia(os(), entregaId, descricao), 'Pendência anotada.'),
    resolverPendencia: (entregaId: number, pendenciaId: number, resolucao: string, data: string | null) =>
      executar(() => servico.resolverPendencia(os(), entregaId, pendenciaId, resolucao, data), 'Pendência resolvida.'),
    reabrirPendencia: (entregaId: number, pendenciaId: number) =>
      executar(() => servico.reabrirPendencia(os(), entregaId, pendenciaId), 'Pendência reaberta.'),
    enviarFoto: (entregaId: number, tipo: 'TERMO' | 'MONTAGEM', arquivo: File) =>
      executar(() => servico.enviarFoto(os(), entregaId, tipo, arquivo)),
    excluirFoto: (entregaId: number, fotoId: number) =>
      executar(() => servico.excluirFoto(os(), entregaId, fotoId), 'Foto excluída.'),
  };
}
