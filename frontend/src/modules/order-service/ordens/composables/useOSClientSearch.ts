import { ref, watch } from 'vue';
import type { Ref } from 'vue';
import { refDebounced } from '@vueuse/core';
import { searchClientes, type ClienteSearchResult } from '@/shared/services/cliente.service';

// Singleton ref that can be updated externally when a new client is created
const lastCreatedId = ref<number | null>(null);

export function useOSClientSearch(isOpen: Ref<boolean>) {
  const searchQuery = ref('');
  const debouncedSearch = refDebounced(searchQuery, 400);
  const clientes = ref<ClienteSearchResult[]>([]);
  const isLoading = ref(false);

  async function fetchClientes() {
    isLoading.value = true;
    try {
      clientes.value = await searchClientes(debouncedSearch.value || undefined);
    } catch {
      clientes.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  watch(isOpen, (open) => {
    if (open) {
      fetchClientes();
    }
  });

  watch(debouncedSearch, () => {
    if (isOpen.value) {
      fetchClientes();
    }
  });

  return {
    searchQuery,
    clientes,
    isLoading,
    lastCreatedId,
  };
}
