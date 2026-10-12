/**
 * @fileoverview Detalhe de UM orçamento, com versões, histórico, anexos e
 * projetos do cliente (Spec 06B D11, D21, D42, D43).
 *
 * Atualização entre computadores (D11): o detalhe recarrega a cada
 * REFETCH_REALTIME SÓ quando nada está esperando para salvar. Recarregar no
 * meio da digitação apagaria o que o usuário acabou de escrever.
 */
import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { REFETCH_REALTIME } from '@/core/config/queryIntervals';

import { chaveAnexos, chaveDetalhe, chaveHistorico, chaveProjetos, chaveVersoes } from '../constants/orcamento.constants';
import { listarAnexos } from '../services/orcamentoAnexos.service';
import { getHistorico, getOrcamento, getProjetosDoCliente, getVersoes } from '../services/orcamento.service';

/**
 * @param id          id do orçamento (null na tela "novo": nada é buscado)
 * @param temPendencia true enquanto há campo esperando salvar ou escrita na fila
 */
export function useOrcamentoQuery(id: Ref<number | null>, temPendencia: Ref<boolean>) {
  return useQuery({
    // A chave usa o valor ATUAL do id: trocar de versão troca a query sozinho.
    queryKey: computed(() => chaveDetalhe(id.value ?? 0)),
    queryFn: () => getOrcamento(id.value!),
    enabled: computed(() => id.value != null),
    // Função: o TanStack pergunta de novo a cada ciclo; com pendência, não recarrega.
    refetchInterval: () => (temPendencia.value ? false : REFETCH_REALTIME),
    retry: 1,
  });
}

/** Todas as versões do mesmo código (menu "v2 ▾", D42). Só busca quando o menu abre. */
export function useVersoesQuery(id: Ref<number | null>, aberto: Ref<boolean>) {
  return useQuery({
    queryKey: computed(() => chaveVersoes(id.value ?? 0)),
    queryFn: () => getVersoes(id.value!),
    enabled: computed(() => id.value != null && aberto.value),
  });
}

/** Eventos de todas as versões (gaveta "Histórico", D43). Só busca quando a gaveta abre. */
export function useHistoricoQuery(id: Ref<number | null>, aberto: Ref<boolean>) {
  return useQuery({
    queryKey: computed(() => chaveHistorico(id.value ?? 0)),
    queryFn: () => getHistorico(id.value!),
    enabled: computed(() => id.value != null && aberto.value),
  });
}

/** Anexos da medição (D44). Valem para todas as versões do código (06A D30). */
export function useAnexosQuery(id: Ref<number | null>) {
  return useQuery({
    queryKey: computed(() => chaveAnexos(id.value ?? 0)),
    queryFn: () => listarAnexos(id.value!),
    enabled: computed(() => id.value != null),
  });
}

/** Projetos que o cliente já tem (D21). Sem cliente, nada é buscado. */
export function useProjetosDoClienteQuery(clienteId: Ref<number | null>) {
  return useQuery({
    queryKey: computed(() => chaveProjetos(clienteId.value ?? 0)),
    queryFn: () => getProjetosDoCliente(clienteId.value!),
    enabled: computed(() => clienteId.value != null),
  });
}
