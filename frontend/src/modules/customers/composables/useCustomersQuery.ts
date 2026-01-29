/**
 * @fileoverview TanStack Query composable for customers list
 * @description Manages customer listing with search and caching
 */

import { computed, type Ref } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';
import { getClientes } from '../services/cliente.service';
import type { Cliente, ClienteFilterStatus } from '../types/clientes.types';

const QUERY_KEY = 'clientes';
const STALE_TIME = 1000 * 60 * 5; // 5 minutes

/**
 * Query for listing customers
 * @param searchTerm - Optional reactive search term
 * @param statusFilter - Optional reactive status filter
 */
export function useCustomersQuery(
  searchTerm?: Ref<string>,
  statusFilter?: Ref<ClienteFilterStatus>
) {
  const cleanSearch = computed(() => searchTerm?.value?.trim() || undefined);
  const cleanStatus = computed(() => statusFilter?.value || 'ativos');

  return useQuery({
    queryKey: [QUERY_KEY, cleanSearch, cleanStatus],
    queryFn: () => getClientes(cleanSearch.value, cleanStatus.value),
    staleTime: STALE_TIME,
  });
}

/**
 * Get query client for manual cache operations
 */
export function useCustomersQueryClient() {
  const queryClient = useQueryClient();

  function invalidateCustomers() {
    queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
  }

  function setCustomersData(data: Cliente[]) {
    queryClient.setQueryData([QUERY_KEY], data);
  }

  return {
    invalidateCustomers,
    setCustomersData,
    queryClient,
  };
}

/**
 * Export query key for external use
 */
export { QUERY_KEY as CUSTOMERS_QUERY_KEY };
