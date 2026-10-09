/**
 * @fileoverview Lista de orçamentos e contagens dos chips (Spec 06B D48, §6.1).
 * A lista recarrega sempre no mesmo intervalo (D11): nada é digitado nela.
 */
import { computed, type Ref } from 'vue';
import { keepPreviousData, useQuery } from '@tanstack/vue-query';

import { REFETCH_REALTIME } from '@/core/config/queryIntervals';

import { chaveContagens, chaveLista } from '../constants/orcamento.constants';
import { getContagens, listarOrcamentos, type FiltrosLista } from '../services/orcamento.service';

export function useOrcamentosQuery(filtros: Ref<FiltrosLista>) {
  return useQuery({
    // Os filtros entram na chave: cada combinação tem o seu cache.
    queryKey: computed(() => chaveLista({ ...filtros.value })),
    queryFn: () => listarOrcamentos(filtros.value),
    placeholderData: keepPreviousData,     // troca de página sem a tabela piscar vazia
    refetchInterval: REFETCH_REALTIME,
  });
}

/** Quantos orçamentos por status ("Rascunho 3", "Vence em 3 dias 2"...). */
export function useContagensQuery() {
  return useQuery({
    queryKey: chaveContagens(),
    queryFn: getContagens,
    refetchInterval: REFETCH_REALTIME,
  });
}
