import { ref, computed, watch } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';
import type { OrdemServicoListRead, OrdemServicoStatus } from '../types/ordemServico.types';
import type { PaginatedResponse } from '../services/ordemServico.service';
import { ordemServicoService } from '../services/ordemServico.service';
import {
  STORAGE_KEY_OS_FILTER,
  OS_ITEMS_PER_PAGE,
  SEARCH_DEBOUNCE_MS,
  OS_LIST_STALE_TIME,
  OS_STATS_STALE_TIME,
} from '../constants/ordemServico.constants';
import {
  ORDENS_SERVICO_QUERY_KEY,
  ORDENS_SERVICO_STATS_QUERY_KEY,
} from '../../shared/constants/queryKeys';

export type FilterStatus = 'todos' | OrdemServicoStatus;

export function useOrdensServico() {
  const savedStatus = localStorage.getItem(STORAGE_KEY_OS_FILTER);
  const activeFilterStatus = ref<FilterStatus>((savedStatus as FilterStatus) || 'todos');

  const searchQuery = ref('');
  const debouncedSearchQuery = refDebounced(searchQuery, SEARCH_DEBOUNCE_MS);
  const currentPage = ref(1);

  watch(debouncedSearchQuery, () => {
    currentPage.value = 1;
  });

  const {
    data: paginatedData,
    isLoading,
    error,
    refetch,
  } = useQuery<PaginatedResponse<OrdemServicoListRead>>({
    queryKey: computed(() => [
      ORDENS_SERVICO_QUERY_KEY,
      activeFilterStatus.value,
      debouncedSearchQuery.value,
      currentPage.value,
    ]),
    queryFn: () => ordemServicoService.getAll({
      status: activeFilterStatus.value,
      buscar: debouncedSearchQuery.value || undefined,
      page: currentPage.value,
      limit: OS_ITEMS_PER_PAGE,
    }),
    staleTime: OS_LIST_STALE_TIME,
  });

  const ordensServico = computed(() => paginatedData.value?.items || []);
  const totalItems = computed(() => paginatedData.value?.total || 0);
  const totalPages = computed(() => paginatedData.value?.pages || 0);

  const { data: statsData } = useQuery<Record<string, number>>({
    queryKey: [ORDENS_SERVICO_STATS_QUERY_KEY],
    queryFn: () => ordemServicoService.getEstatisticas(),
    staleTime: OS_STATS_STALE_TIME,
  });

  const stats = computed(() => {
    const s = statsData.value || {};
    const total = Object.values(s).reduce((acc: number, val: number) => acc + (Number(val) || 0), 0);
    return {
      total,
      abertas: (s['ABERTA'] || 0),
      emAndamento: (s['EM_ANDAMENTO'] || 0) + (s['AGUARDANDO_PECAS'] || 0) + (s['AGUARDANDO_APROVACAO'] || 0) + (s['AGUARDANDO_RETIRADA'] || 0),
      finalizadas: (s['FINALIZADA'] || 0),
    };
  });

  function setFilterStatus(status: FilterStatus): void {
    activeFilterStatus.value = status;
    localStorage.setItem(STORAGE_KEY_OS_FILTER, status);
    currentPage.value = 1;
  }

  function setSearch(query: string): void {
    searchQuery.value = query;
  }

  function setPage(page: number): void {
    if (page >= 1 && (totalPages.value === 0 || page <= totalPages.value)) {
      currentPage.value = page;
    }
  }

  return {
    ordensServico,
    stats,
    activeFilterStatus,
    searchQuery,
    isLoading,
    error,
    setFilterStatus,
    setSearch,
    refetch,
    currentPage,
    totalPages,
    totalItems,
    setPage,
  };
}
