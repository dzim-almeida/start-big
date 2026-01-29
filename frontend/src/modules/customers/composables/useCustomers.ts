/**
 * @fileoverview Combined composable for customers module
 * @description Combines query and filters for easy use in views
 */

import { ref, watch } from 'vue';
import { useCustomersQuery } from './useCustomersQuery';
import { useCustomerFilters } from './useCustomerFilters';
import type { ClienteFilterStatus } from '../types/clientes.types';

/**
 * Combined composable for customer list management
 * Integrates TanStack Query with local filtering and pagination
 */
export function useCustomers() {
  // Search term for API query
  const searchTerm = ref('');
  const statusFilter = ref<ClienteFilterStatus>('ativos');

  // Query
  const { data: customersData, isLoading, refetch } = useCustomersQuery(
    searchTerm,
    statusFilter
  );

  // Filters and pagination
  const filters = useCustomerFilters(customersData);

  // Sync status filter with query
  watch(
    () => filters.activeFilterStatus.value,
    (newStatus) => {
      statusFilter.value = newStatus;
    }
  );

  // Override setSearch to also update the API search term
  function setSearch(query: string): void {
    searchTerm.value = query;
    filters.setSearch(query);
    refetch();
  }

  // Override setFilterStatus to trigger refetch
  function setFilterStatus(status: ClienteFilterStatus): void {
    filters.setFilterStatus(status);
    refetch();
  }

  return {
    // From query
    isLoading,
    refetch,

    // From filters
    customers: filters.customers,
    stats: filters.stats,
    activeFilterTipo: filters.activeFilterTipo,
    activeFilterStatus: filters.activeFilterStatus,
    searchQuery: filters.searchQuery,
    currentPage: filters.currentPage,
    totalItems: filters.totalItems,
    totalPages: filters.totalPages,

    // Actions
    setFilterTipo: filters.setFilterTipo,
    setFilterStatus,
    setSearch,
    setPage: filters.setPage,
    resetFilters: filters.resetFilters,
  };
}
