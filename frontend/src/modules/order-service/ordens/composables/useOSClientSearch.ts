import { ref, computed, watch, type Ref } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useQuery, useQueryClient } from '@tanstack/vue-query';
import { searchClientes, type ClienteSearchResult } from '@/shared/services/cliente.service';
import { useCustomerModal } from '@/modules/customers/composables/useCustomerModal';
import { CLIENTES_SEARCH_QUERY_KEY } from '../../shared/constants/queryKeys';

export function useOSClientSearch(isOpen: Ref<boolean>) {
  const searchQuery = ref('');
  const debouncedSearch = refDebounced(searchQuery, 300);
  const lastCreatedId = ref<number | null>(null);
  const queryClient = useQueryClient();
  const { isOpen: isCustomerModalOpen } = useCustomerModal();

  const { data: clientesData, isLoading } = useQuery({
    queryKey: computed(() => [CLIENTES_SEARCH_QUERY_KEY, debouncedSearch.value]),
    queryFn: () => searchClientes(debouncedSearch.value || undefined),
    enabled: computed(() => isOpen.value),
    staleTime: 1000 * 30,
  });

  // Quando CustomerFormModal fechar → refetch para incluir o novo cliente
  watch(isCustomerModalOpen, (open, wasOpen) => {
    if (!open && wasOpen) {
      queryClient.invalidateQueries({ queryKey: [CLIENTES_SEARCH_QUERY_KEY] });
    }
  });

  // Detectar cliente recém-criado: novo item na lista após refetch
  watch(clientesData, (newData, oldData) => {
    if (!isCustomerModalOpen.value && newData && oldData && newData.length > oldData.length) {
      const oldIds = new Set(oldData.map((c) => c.id));
      const added = newData.find((c) => !oldIds.has(c.id));
      if (added) lastCreatedId.value = added.id;
    }
  });

  // Reset ao fechar o modal de seleção
  watch(isOpen, (open) => {
    if (!open) {
      searchQuery.value = '';
      lastCreatedId.value = null;
    }
  });

  const clientes = computed<ClienteSearchResult[]>(() => clientesData.value ?? []);

  return {
    searchQuery,
    clientes,
    isLoading,
    lastCreatedId,
  };
}
