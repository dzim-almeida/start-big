/**
 * @fileoverview A separação de uma OS: a leitura e as ações (Spec 10B D12, D13).
 *
 * - A query só roda com a aba ABERTA (os outros segmentos nunca chamam
 *   `/marcenaria/...`) e recarrega a cada `REFETCH_REALTIME` enquanto nenhum
 *   modal da aba estiver aberto: duas pessoas separando veem o progresso uma
 *   da outra (D13).
 * - Toda ação manda o retirado que a tela mostrava; se outra pessoa mexeu na
 *   linha (409 REVISAO_DESATUALIZADA), avisa, recarrega e NÃO tenta de novo (D12).
 */
import { computed, ref, type Ref } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';

import { REFETCH_REALTIME } from '@/core/config/queryIntervals';
import { useToast } from '@/shared/composables/useToast';
import { codigoDoErro, mensagemDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';

import type { LinhaSeparacao, Separacao } from '../schemas/separacao.schema';
import * as servico from '../services/separacao.service';

/** A chave do cache da separação de uma OS. */
export const chaveSeparacao = (numeroOs: string) => ['marcenaria', 'separacao', numeroOs] as const;

/** A frase do conflito (D12): a mesma do backend. */
export const MSG_CONFLITO = 'Outra pessoa alterou este item. A lista foi atualizada.';

export function useSeparacao(numeroOs: Ref<string>, ativo: Ref<boolean>, pausado: Ref<boolean>) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const consulta = useQuery({
    queryKey: computed(() => chaveSeparacao(numeroOs.value)),
    queryFn: () => servico.getSeparacao(numeroOs.value),
    enabled: computed(() => ativo.value && !!numeroOs.value),
    // Função: o TanStack pergunta de novo a cada ciclo; com modal aberto, não recarrega.
    refetchInterval: () => (pausado.value ? false : REFETCH_REALTIME),
    retry: false,                                    // 404 (OS sem orçamento) não melhora repetindo
  });

  const gravando = ref(false);

  /** Roda a ação, guarda a resposta no cache e trata o erro. Null = não gravou. */
  async function executar(acao: () => Promise<Separacao>, sucesso?: string): Promise<Separacao | null> {
    gravando.value = true;
    try {
      const nova = await acao();
      queryClient.setQueryData(chaveSeparacao(numeroOs.value), nova);   // a tela já mostra o novo
      if (sucesso) toast.success(sucesso);
      return nova;
    } catch (erro) {
      if (codigoDoErro(erro) === 'REVISAO_DESATUALIZADA') {
        toast.error(MSG_CONFLITO);
        await queryClient.invalidateQueries({ queryKey: chaveSeparacao(numeroOs.value) });   // recarrega
      } else {
        toast.error(mensagemDoErro(erro));
      }
      return null;
    } finally {
      gravando.value = false;
    }
  }

  const os = () => numeroOs.value;
  return {
    ...consulta,
    gravando,
    retirarLinha: (linha: LinhaSeparacao, quantidade: number) =>
      executar(() => servico.retirar(os(), linha.item_id, quantidade, linha.separada_milesimos)),
    devolverLinha: (linha: LinhaSeparacao, quantidade: number) =>
      executar(() => servico.devolver(os(), linha.item_id, quantidade, linha.separada_milesimos), 'Devolvido ao estoque.'),
    concluirLinha: (linha: LinhaSeparacao) =>
      executar(() => servico.concluir(os(), linha.item_id, linha.separada_milesimos)),
    reabrirLinha: (linha: LinhaSeparacao) =>
      executar(() => servico.reabrir(os(), linha.item_id, linha.separada_milesimos)),
  };
}
