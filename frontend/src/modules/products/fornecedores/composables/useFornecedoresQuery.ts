import { computed, ref, watch } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';

import { getFornecedores } from '../services/fornecedor.service';
import { FORNECEDORES_QUERY_KEY, FORNECEDORES_STALE_TIME } from '../constants/fornecedor.constants';
import type { StatusFilter } from '../types/fornecedor.types';
import type { FornecedorReadType } from '../schemas/fornecedor.schema';

export function useFornecedoresQuery() {
  const searchQuery = ref<string>('');
  const debouncedSearchQuery = refDebounced(searchQuery, 400);
  const activeFilterQuery = ref<StatusFilter | null>(null);

  const query = useQuery({
    queryKey: [FORNECEDORES_QUERY_KEY, debouncedSearchQuery],
    queryFn: () => getFornecedores(debouncedSearchQuery.value || undefined),
    staleTime: FORNECEDORES_STALE_TIME,
  });

  const allFornecedores = computed<FornecedorReadType[]>(() => query.data.value ?? []);

  const fornecedores = computed<FornecedorReadType[]>(() => {
    if (!activeFilterQuery.value) return allFornecedores.value;
    const isAtivo = activeFilterQuery.value === 'ativos';
    return allFornecedores.value.filter((f) => f.ativo === isAtivo);
  });

  const stats = computed(() => ({
    total: allFornecedores.value.length,
    ativos: allFornecedores.value.filter((f) => f.ativo).length,
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
