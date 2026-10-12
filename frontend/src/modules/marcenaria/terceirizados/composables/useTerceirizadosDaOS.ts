/**
 * @fileoverview Os móveis terceirizados de uma OS: a leitura e as ações
 * (Spec 11B D1-D9, §7.3).
 *
 * - A query só roda com a aba Separação ABERTA (os outros segmentos nunca
 *   chamam `/marcenaria/...`). OS sem orçamento devolve 404: a seção some.
 * - Toda ação devolve a seção atualizada (11A §6): ela entra direto no cache,
 *   sem esperar outro GET.
 * - Depois de cada ação, a lista da aba "Terceirizados" (Serviços) e a aba
 *   Produção (12B, o terceirizado conferido aparece pronto) ficam velhas:
 *   são invalidadas para recarregar quando forem abertas.
 */
import { computed, ref, type Ref } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';

import { useToast } from '@/shared/composables/useToast';
import { mensagemDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';

import type { PedirResposta, TerceirizadosDaOS } from '../schemas/terceirizado.schema';
import * as servico from '../services/terceirizado.service';

/** A chave do cache da seção de uma OS. */
export const chaveTerceirizadosDaOS = (numeroOs: string) => ['marcenaria', 'terceirizados', 'os', numeroOs] as const;
/** O começo da chave da lista geral (aba "Terceirizados"): invalida todos os filtros de uma vez. */
export const CHAVE_LISTA_TERCEIRIZADOS = ['marcenaria', 'terceirizados', 'lista'] as const;
/** O começo da chave da aba Produção (12B). */
export const CHAVE_PRODUCAO = ['marcenaria', 'producao'] as const;

export function useTerceirizadosDaOS(numeroOs: Ref<string>, ativo: Ref<boolean>) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const consulta = useQuery({
    queryKey: computed(() => chaveTerceirizadosDaOS(numeroOs.value)),
    queryFn: () => servico.getTerceirizados(numeroOs.value),
    enabled: computed(() => ativo.value && !!numeroOs.value),
    retry: false,                                    // 404 (OS sem orçamento) não melhora repetindo
  });

  /** Verdadeiro enquanto uma ação está no servidor (os botões mostram "carregando"). */
  const gravando = ref(false);

  /** Guarda a seção nova no cache e marca as outras telas como velhas. */
  function aplicar(nova: TerceirizadosDaOS) {
    queryClient.setQueryData(chaveTerceirizadosDaOS(numeroOs.value), nova);   // a tela já mostra o novo
    void queryClient.invalidateQueries({ queryKey: CHAVE_LISTA_TERCEIRIZADOS });
    void queryClient.invalidateQueries({ queryKey: CHAVE_PRODUCAO });
  }

  /**
   * Roda a ação, aplica a resposta e mostra o erro em toast.
   * Devolve a resposta (com a `sugestao_status` do conferir/voltar) ou null se não gravou.
   */
  async function executar<T>(
    acao: () => Promise<T>, extrairSecao: (resposta: T) => TerceirizadosDaOS, sucesso?: string,
  ): Promise<T | null> {
    gravando.value = true;
    try {
      const resposta = await acao();
      aplicar(extrairSecao(resposta));
      if (sucesso) toast.success(sucesso);
      return resposta;
    } catch (erro) {
      toast.error(mensagemDoErro(erro));
      // Outra pessoa pode ter mexido no móvel (409): recarrega para a tela dizer a verdade.
      await queryClient.invalidateQueries({ queryKey: chaveTerceirizadosDaOS(numeroOs.value) });
      return null;
    } finally {
      gravando.value = false;
    }
  }

  // Atalhos: a resposta das ações comuns JÁ é a seção.
  const mesma = (secao: TerceirizadosDaOS) => secao;
  const os = () => numeroOs.value;

  return {
    ...consulta,
    gravando,
    /** Com o Compras (D4): o toast com o atalho para o pedido fica com quem chamou. */
    pedir: (movelIds: number[], previsao: string | null, observacao: string | null): Promise<PedirResposta | null> =>
      executar(() => servico.pedir(os(), movelIds, previsao, observacao), (r) => r.terceirizados),
    /** Sem o Compras (D6). */
    enviarManual: (movelIds: number[], pedido: string | null, previsao: string | null) =>
      executar(() => servico.enviarManual(os(), movelIds, pedido, previsao), mesma, 'Pedido à central anotado.'),
    receberManual: (movelIds: number[], data: string | null) =>
      executar(() => servico.receberManual(os(), movelIds, data), mesma, 'Chegada anotada.'),
    /** Nos dois modos (D7). */
    conferir: (movelIds: number[]) =>
      executar(() => servico.conferir(os(), movelIds), mesma, 'Móveis conferidos.'),
    registrarProblema: (movelId: number, texto: string) =>
      executar(() => servico.registrarProblema(os(), movelId, texto), mesma, 'Problema registrado.'),
    voltar: (movelId: number) =>
      executar(() => servico.voltar(os(), movelId), mesma, 'Voltou um passo.'),
  };
}
