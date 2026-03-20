import { ref, computed } from 'vue';

import { useCustomerQueryAll } from './request/useCustomerGet.queries';

import type {
  ClienteFormatted,
  ClienteStatsData,
  CustomersTypes,
} from '../types/clientes.types';

import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';
import { isCustomerPF } from '@/shared/schemas/customer/customer.schema';
import { getInitials } from '@/shared/utils/string.utils';

// ── Helpers ────────────────────────────────────────────────────────────────

function formatCustomer(customer: CustomerUnionReadSchemaDataType): ClienteFormatted {
  const name = isCustomerPF(customer) ? customer.nome : customer.nome_fantasia;
  const doc = isCustomerPF(customer) ? customer.cpf : customer.cnpj;

  return {
    ...customer,
    displayName: name || 'Sem Nome',
    displayDoc: doc || '',
    displayPhone: customer.celular || customer.telefone || '',
    initial: getInitials(name || ''),
    sortName: (name || '').toLowerCase(),
  } as ClienteFormatted;
}

function calculateStats(customers: CustomerUnionReadSchemaDataType[]): ClienteStatsData {
  return {
    total: customers.length,
    ativos: customers.filter((c) => c.ativo).length,
    pf: customers.filter((c) => c.tipo === 'PF').length,
    pj: customers.filter((c) => c.tipo === 'PJ').length,
  };
}

// ── Composable ─────────────────────────────────────────────────────────────

export function useCustomers() {
  const {
    searchQuery,
    customers: rawCustomers,
    totalPages,
    totalItems,
    currentPage,
    isLoading,
    setPage,
  } = useCustomerQueryAll();

  // Filtro local por tipo (PF/PJ/active/inactive) — backend não suporta
  const activeFilterTipo = ref<CustomersTypes>(null);

  const filteredCustomers = computed<ClienteFormatted[]>(() => {
    let result = rawCustomers.value;

    if (activeFilterTipo.value !== null) {
      result = result.filter((c) => {
        if (activeFilterTipo.value === 'active') return c.ativo;
        if (activeFilterTipo.value === 'inactive') return !c.ativo;
        return c.tipo === activeFilterTipo.value;
      });
    }

    return result
      .map(formatCustomer)
      .sort((a, b) => a.sortName.localeCompare(b.sortName, 'pt-BR'));
  });

  const stats = computed<ClienteStatsData>(() => calculateStats(rawCustomers.value));

  return {
    customers: filteredCustomers,
    stats,
    searchQuery,
    activeFilterTipo,
    isLoading,
    currentPage,
    totalPages,
    totalItems,
    setPage,
  };
}
