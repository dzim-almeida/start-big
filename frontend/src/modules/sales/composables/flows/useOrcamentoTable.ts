import { ref, computed, watch } from 'vue';
import { refDebounced } from '@vueuse/core';

import { useOrcamentosListQuery } from '../queries/useOrcamentosListQuery';

export function useOrcamentoTable() {
  const searchTerm = ref<string | null>(null);
  const debouncedSearchTerm = refDebounced(searchTerm, 300);
  const activeFilter = ref<string | null>(null);
  const page = ref<number>(1);

  watch([searchTerm, activeFilter], () => {
    page.value = 1;
  });

  const filters = computed(() => {
    const convertidoMap: Record<string, boolean> = { ATIVO: false, CONVERTIDO: true };
    return {
      ...(debouncedSearchTerm.value && { search: debouncedSearchTerm.value }),
      ...(activeFilter.value && activeFilter.value in convertidoMap && { convertido: convertidoMap[activeFilter.value] }),
    };
  });

  const goToPage = (newPage: number) => {
    page.value = newPage;
  };

  const { data: orcamentos, isLoading } = useOrcamentosListQuery(filters, page);

  return {
    searchTerm,
    activeFilter,
    goToPage,
    orcamentos,
    isLoading,
  };
}
