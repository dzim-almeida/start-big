import { ref, computed, watch, type Ref } from 'vue';
import { useClientes } from '@/modules/clientes/composables/useClientes';
import type { Cliente } from '@/modules/clientes/types/clientes.types';

export function useOSClientSearch(isOpen: Ref<boolean>) {
  const {
    clientes: allClientes,
    isLoading,
    setSearch,
    setOnlyActive
  } = useClientes();

  setOnlyActive(true);

  const searchQuery = ref('');
  const selectedClienteId = ref<number | null>(null);

  watch(searchQuery, (newValue) => {
    setSearch(newValue);
    selectedClienteId.value = null;
  });

  watch(isOpen, (newVal) => {
    if (!newVal) {
      reset();
    }
  });

  const filteredClientes = computed<Cliente[]>(() => {
    if (!searchQuery.value.trim()) {
      return [];
    }
    return (allClientes.value || []).slice(0, 20);
  });

  function reset() {
    searchQuery.value = '';
    selectedClienteId.value = null;
    setSearch('');
  }

  return {
    searchQuery,
    selectedClienteId,
    filteredClientes,
    isLoading,
    reset
  };
}
