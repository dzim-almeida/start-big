// ============================================================================
// MÓDULO: FornecedorQuery (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Gerenciar a busca, cache e filtragem de fornecedores.
// TECNOLOGIAS: Vue Query (TanStack), VueUse (Debounce), Computed Properties.
// FUNCIONALIDADES: Busca debounced (400ms), filtragem por status local, 
//                  cálculo de estatísticas e gestão de estado de carregamento.
// ============================================================================
import { computed, ref } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';

import { getFornecedores } from '../services/fornecedor.service';
import { FORNECEDORES_QUERY_KEY, FORNECEDORES_STALE_TIME } from '../../shared/constants/queryKeys';
import type { StatusFilter } from '../types/fornecedor.types';
import type { FornecedorReadType } from '../schemas/fornecedor.schema';

export function useFornecedoresQuery() {
  const searchQuery = ref<string>('');
  const debouncedSearchQuery = refDebounced(searchQuery, 400);
  const activeFilterQuery = ref<StatusFilter | null>(null);

  const query = useQuery({
    queryKey: computed(() => [FORNECEDORES_QUERY_KEY, debouncedSearchQuery.value]),
    queryFn: () => getFornecedores(debouncedSearchQuery.value || undefined),
    staleTime: FORNECEDORES_STALE_TIME,
  });

  const allFornecedores = computed<FornecedorReadType[]>(() => query.data.value ?? []);

  const fornecedores = computed<FornecedorReadType[]>(() => {
    if (!activeFilterQuery.value) return allFornecedores.value;
    if (activeFilterQuery.value === 'ativos') return allFornecedores.value.filter((f) => !!f.ativo);
    if (activeFilterQuery.value === 'inativos') return allFornecedores.value.filter((f) => !f.ativo);
    return allFornecedores.value;
  });

  const stats = computed(() => ({
    total: allFornecedores.value.length,
    ativos: allFornecedores.value.filter((f) => !!f.ativo).length,
    inativos: allFornecedores.value.filter((f) => !f.ativo).length,
  }));

  return {
    searchQuery,
    activeFilterQuery,
    fornecedores,
    stats,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
