/**
 * @fileoverview Customer filters and pagination composable
 * @description Manages local filtering, formatting, and pagination for customer list
 */

import { ref, computed, type Ref } from 'vue';
import type {
  Cliente,
  ClienteFormatted,
  ClienteFilterStatus,
  ClienteStatsData,
  CustomersTypes,
} from '../types/clientes.types';
import { getInitials } from '@/shared/utils/string.utils';

const ITEMS_PER_PAGE = 10;

function getCustomersStatus(customers: Cliente) {
  return customers.ativo ? 'active' : 'inactive';
}

/**
 * Composable for managing customer filters and pagination
 * @param customersData - Reactive ref to raw customer data from query
 */
export function useCustomerFilters(customersData: Ref<Cliente[] | undefined>) {
  // =============================================
  // State
  // =============================================

  const activeFilterTipo = ref<CustomersTypes>(null);
  const activeFilterStatus = ref<ClienteFilterStatus>('ativos');
  const searchQuery = ref('');
  const currentPage = ref(1);

  // =============================================
  // Computed: Filtered List
  // =============================================

  const filteredCustomers = computed(() => {
    let result = customersData.value || [];

    // Filter by type (PF/PJ)
    if (activeFilterTipo.value !== null) {
      result = result.filter((c) => {
        return c.tipo === activeFilterTipo.value || getCustomersStatus(c) === activeFilterTipo.value;
      });
    }

    // Filter by search text
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase().trim();
      const queryNumbers = query.replace(/\D/g, '');

      result = result.filter((c) => {
        const nome = c.tipo === 'PF' ? c.nome : c.nome_fantasia;
        const doc = c.tipo === 'PF' ? c.cpf : c.cnpj;

        if (nome && nome.toLowerCase().includes(query)) return true;
        if (c.email && c.email.toLowerCase().includes(query)) return true;
        if (doc && queryNumbers && doc.includes(queryNumbers)) return true;

        if (queryNumbers) {
          if (c.celular && c.celular.replace(/\D/g, '').includes(queryNumbers)) return true;
          if (c.telefone && c.telefone.replace(/\D/g, '').includes(queryNumbers)) return true;
        }

        return false;
      });
    }

    return result;
  });

  // =============================================
  // Computed: Formatted List
  // =============================================

  const formattedCustomers = computed<ClienteFormatted[]>(() => {
    const lista = filteredCustomers.value;
    if (!lista || !Array.isArray(lista)) return [];

    const mapped = lista.map((cliente) => {
      const c = cliente as any;
      const name = cliente.tipo === 'PF' ? c.nome : c.nome_fantasia;

      return {
        ...cliente,
        displayName: name || 'Sem Nome',
        displayDoc: cliente.tipo === 'PF' ? c.cpf || '' : c.cnpj || '',
        displayPhone: cliente.celular || cliente.telefone || '',
        initial: getInitials(name),
        sortName: (name || '').toLowerCase(),
      } as ClienteFormatted;
    });

    return mapped.sort((a, b) => a.sortName.localeCompare(b.sortName, 'pt-BR'));
  });

  // =============================================
  // Computed: Pagination
  // =============================================

  const totalItems = computed(() => formattedCustomers.value.length);
  const totalPages = computed(() => Math.ceil(totalItems.value / ITEMS_PER_PAGE));

  const paginatedCustomers = computed(() => {
    const start = (currentPage.value - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    return formattedCustomers.value.slice(start, end);
  });

  // =============================================
  // Computed: Statistics
  // =============================================

  const stats = computed<ClienteStatsData>(() => {
    const data = customersData.value || [];
    return {
      total: data.length,
      ativos: data.filter((c) => c.ativo).length,
      pf: data.filter((c) => c.tipo === 'PF').length,
      pj: data.filter((c) => c.tipo === 'PJ').length,
    };
  });

  // =============================================
  // Actions
  // =============================================

  function setFilterTipo(tipo: CustomersTypes): void {
    activeFilterTipo.value = tipo;
    currentPage.value = 1;
  }

  function setFilterStatus(status: ClienteFilterStatus): void {
    activeFilterStatus.value = status;
    currentPage.value = 1;
  }

  function setSearch(query: string): void {
    searchQuery.value = query;
    currentPage.value = 1;
  }

  function setPage(page: number): void {
    currentPage.value = page;
  }

  function resetFilters(): void {
    activeFilterTipo.value = null;
    activeFilterStatus.value = 'ativos';
    searchQuery.value = '';
    currentPage.value = 1;
  }

  // =============================================
  // Return
  // =============================================

  return {
    // State
    activeFilterTipo,
    activeFilterStatus,
    searchQuery,
    currentPage,

    // Computed
    customers: paginatedCustomers,
    totalItems,
    totalPages,
    stats,

    // Actions
    setFilterTipo,
    setFilterStatus,
    setSearch,
    setPage,
    resetFilters,
  };
}
