import { ref, computed, watch } from 'vue';
import type { Ref, ComputedRef } from 'vue';
import { refDebounced } from '@vueuse/core';

import { useOsCustomersGet } from './useOSRelationshipGet.queries';
import type { CustomerUnionReadSchemaDataType } from '../../../schemas/relationship/customer/customer.schema';

export function useOSClientSearch(isOpen: Ref<boolean>): {
  searchQuery: Ref<string>;
  clientes: ComputedRef<CustomerUnionReadSchemaDataType[]>;
  isLoading: Ref<boolean>;
  lastCreatedId: Ref<number | null>;
} {
  const searchQuery = ref('');
  const debouncedQuery = refDebounced(searchQuery, 400);
  const lastCreatedId = ref<number | null>(null);

  const { data, isLoading } = useOsCustomersGet();

  // Resetar pesquisa ao fechar
  watch(isOpen, (open) => {
    if (!open) searchQuery.value = '';
  });

  const clientes = computed<CustomerUnionReadSchemaDataType[]>(() => {
    const all = data.value ?? [];
    const q = debouncedQuery.value.trim().toLowerCase();
    if (!q) return all;
    return all.filter((c) => {
      const cf = c as { tipo: string; nome?: string; nome_fantasia?: string; razao_social?: string; cpf?: string; cnpj?: string };
      const name = cf.tipo === 'PF'
        ? (cf.nome ?? '')
        : (cf.nome_fantasia ?? cf.razao_social ?? '');
      const doc = cf.tipo === 'PF' ? (cf.cpf ?? '') : (cf.cnpj ?? '');
      return name.toLowerCase().includes(q) || doc.includes(q);
    });
  });

  return { searchQuery, clientes, isLoading: isLoading as Ref<boolean>, lastCreatedId };
}
