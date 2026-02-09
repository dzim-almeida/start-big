import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import {
  SEARCH_DEBOUNCE_MS,
  SERVICOS_QUERY_KEY,
  SERVICOS_STALE_TIME,
} from '../constants/servicos.constants';
import { getServicos } from '../services/servicos.service';
import type { StatusFilter } from '../types/servicos.types';

export function useServicos() {
  const statusFilter = ref<StatusFilter | null>(null);
  const searchQuery = ref('');
  const debouncedSearchQuery = ref('');

  let searchTimeout: ReturnType<typeof setTimeout> | null = null;

  watch(searchQuery, (newValue) => {
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      debouncedSearchQuery.value = newValue;
    }, SEARCH_DEBOUNCE_MS);
  });

  onBeforeUnmount(() => {
    if (searchTimeout) clearTimeout(searchTimeout);
  });

  const {
    data: servicosData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: computed(() => [
      SERVICOS_QUERY_KEY,
      statusFilter.value ?? 'todos',
      debouncedSearchQuery.value,
    ]),
    queryFn: () =>
      getServicos({
        status: statusFilter.value ?? 'todos',
        buscar: debouncedSearchQuery.value.trim() || undefined,
      }),
    staleTime: SERVICOS_STALE_TIME,
  });

  const servicos = computed(() => servicosData.value || []);
  const totalItems = computed(() => servicos.value.length);

  const stats = computed(() => {
    const total = servicos.value.length;
    const ativos = servicos.value.filter((servico) => servico.ativo).length;
    const inativos = total - ativos;
    const totalValor = servicos.value.reduce((acc, servico) => acc + servico.valor, 0);
    const mediaValor = total > 0 ? Math.round(totalValor / total) : 0;

    return {
      total,
      ativos,
      inativos,
      mediaValor,
    };
  });

  function setSearch(query: string): void {
    searchQuery.value = query;
  }

  function setFilter(status: StatusFilter | null): void {
    statusFilter.value = status;
  }

  return {
    servicos,
    stats,
    searchQuery,
    statusFilter,
    isLoading,
    isError,
    error,
    setSearch,
    setFilter,
    refetch,
    totalItems,
  };
}
