import { ref, computed, watch } from 'vue';
import { refDebounced } from '@vueuse/core';

import { useSalesListQuery } from '../queries/useSalesListQuery';

export function useSaleTable() {
  const searchTerm = ref<string | null>(null);
  const debouncedSearchTerm = refDebounced(searchTerm, 300);
  const activeFilter = ref<'ORCAMENTO' | 'FINALIZADA' | 'CANCELADA' | null>(null);
  const page = ref<number>(1);

  watch([searchTerm, activeFilter], () => {
    page.value = 1;
  });

  const filters = computed(() => {
    return {
      ...(debouncedSearchTerm.value && { search: debouncedSearchTerm.value }),
      ...(activeFilter.value && { status: activeFilter.value }),
    };
  });

  const goToPage = (newPage: number) => {
    page.value = newPage;
  };

  const { data: sales, isLoading } = useSalesListQuery(filters, page);

  return {
    searchTerm,
    activeFilter,
    goToPage,
    sales,
    isLoading,
  };
}
