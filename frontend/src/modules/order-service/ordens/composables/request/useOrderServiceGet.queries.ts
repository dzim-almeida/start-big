import { ref, watch, computed } from 'vue';
import type { Ref } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';

import { getAllOs, getUniqueOS, getStatsOS, getOsByClienteId } from '../../services/orderServiceGet.service';

import { OsStatusEnumDataType } from '../../schemas/enums/osEnums.schema';

import {
  ORDER_SERVICE_QUERY_KEY,
  ORDER_SERVICE_QUERY_STALE_TIME,
} from '../../constants/core.constant';

export function useOrderServiceQueryAll() {
  const searchQuery = ref<string | undefined>(undefined);
  const deboucedSearchQuery = refDebounced(searchQuery, 1000);
  const activeStatusFilterQuery = ref<OsStatusEnumDataType | undefined>(undefined);
  const activePriorityFilterQuery = ref<boolean>(false);
  const currentPage = ref<number>(1);

  watch([deboucedSearchQuery, activeStatusFilterQuery, activePriorityFilterQuery], () => {
    currentPage.value = 1;
  });

  const query = useQuery({
    queryKey: [
      ORDER_SERVICE_QUERY_KEY,
      deboucedSearchQuery,
      activeStatusFilterQuery,
      activePriorityFilterQuery,
      currentPage,
    ],
    queryFn: () =>
      getAllOs({
        search: deboucedSearchQuery.value,
        status: activeStatusFilterQuery.value,
        priority_sort: activePriorityFilterQuery.value,
      }),
    staleTime: ORDER_SERVICE_QUERY_STALE_TIME,
  });

  const orderServices = computed(() => query.data.value?.items ?? []);
  const totalPages = computed(() => query.data.value?.total_pages ?? 1);
  const totalItems = computed(() => query.data.value?.total_items ?? 0);

  const setPage = (page: number) => {
    currentPage.value = page;
  };

  return {
    searchQuery,
    activeStatusFilterQuery,
    activePriorityFilterQuery,
    orderServices,
    totalPages,
    totalItems,
    currentPage,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    setPage,
  };
}

export function useOrderServiceQueryUnique(numero_os: string) {
  const query = useQuery({
    queryKey: [ORDER_SERVICE_QUERY_KEY, numero_os],
    queryFn: () => getUniqueOS(numero_os),
    staleTime: ORDER_SERVICE_QUERY_STALE_TIME,
  });

  const uniqueOs = query.data.value;

  return {
    uniqueOs,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}

export function useOrderServiceQueryStats() {
  const query = useQuery({
    queryKey: [ORDER_SERVICE_QUERY_KEY],
    queryFn: () => getStatsOS(),
    staleTime: ORDER_SERVICE_QUERY_STALE_TIME,
  });

  const stats = computed(() => ({
    total: query.data.value?.total ?? 0,
    abertas: query.data.value?.abertas ?? 0,
    finalizadas: query.data.value?.finalizadas ?? 0,
    ticket_medio: query.data.value?.ticket_medio ?? 0,
  }));

  return {
    stats,
    isLoading: query.isLoading,
  };
}

export function useOrderServiceQueryByCliente(clienteId: Ref<number | null>) {
  const currentPage = ref(1);

  const query = useQuery({
    queryKey: [ORDER_SERVICE_QUERY_KEY, 'by-cliente', clienteId, currentPage],
    queryFn: () => getOsByClienteId(clienteId.value!, currentPage.value),
    enabled: computed(() => !!clienteId.value && clienteId.value > 0),
    staleTime: ORDER_SERVICE_QUERY_STALE_TIME,
  });

  return {
    items: computed(() => query.data.value?.items ?? []),
    totalPages: computed(() => query.data.value?.total_pages ?? 1),
    totalItems: computed(() => query.data.value?.total_items ?? 0),
    currentPage,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
