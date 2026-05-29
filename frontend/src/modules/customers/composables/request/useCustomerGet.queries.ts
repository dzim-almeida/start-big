import { ref, watch, computed } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery } from '@tanstack/vue-query';

import { getAllCustomers } from '../../services/customerGet.service';

import {
  CUSTOMER_QUERY_KEY,
  CUSTOMER_QUERY_STALE_TIME,
} from '../../constants/customer.constant';

export function useCustomerQueryAll() {
  const searchQuery = ref('');
  const debouncedSearch = refDebounced(searchQuery, 500);
  const onlyActive = ref<boolean>(true);
  const currentPage = ref<number>(1);

  watch([debouncedSearch, onlyActive], () => {
    currentPage.value = 1;
  });

  const query = useQuery({
    queryKey: [CUSTOMER_QUERY_KEY, debouncedSearch, onlyActive, currentPage],
    queryFn: () =>
      getAllCustomers({
        search: debouncedSearch.value || undefined,
        only_active: onlyActive.value,
        page: currentPage.value,
      }),
    staleTime: CUSTOMER_QUERY_STALE_TIME,
  });

  const customers = computed(() => query.data.value?.items ?? []);
  const totalPages = computed(() => query.data.value?.total_pages ?? 1);
  const totalItems = computed(() => query.data.value?.total_items ?? 0);

  const setPage = (page: number) => {
    currentPage.value = page;
  };

  return {
    searchQuery,
    onlyActive,
    customers,
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
