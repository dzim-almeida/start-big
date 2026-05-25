import { computed } from 'vue';
import { useOrderServiceQueryAll, useOrderServiceQueryStats } from './request/useOrderServiceGet.queries';
import type { OsStatusEnumDataType } from '../schemas/enums/osEnums.schema';

export function useOrdensServico() {
  const {
    searchQuery,
    activeStatusFilterQuery,
    currentPage,
    orderServices,
    totalPages,
    totalItems,
    isLoading,
    error,
    setPage,
  } = useOrderServiceQueryAll();

  const { stats: rawStats } = useOrderServiceQueryStats();

  const stats = computed(() => ({
    total: rawStats.value.total,
    abertas: rawStats.value.abertas,
    emAndamento: 0, // backend não retorna este campo ainda
    finalizadas: rawStats.value.finalizadas,
  }));

  function setFilterStatus(status: OsStatusEnumDataType | 'todos') {
    activeStatusFilterQuery.value = status === 'todos' ? undefined : status;
  }

  const activeFilterStatus = computed<OsStatusEnumDataType | 'todos'>(
    () => activeStatusFilterQuery.value ?? 'todos',
  );

  return {
    ordensServico: orderServices,
    stats,
    activeFilterStatus,
    searchQuery,
    isLoading,
    error,
    setFilterStatus,
    currentPage,
    totalPages,
    totalItems,
    setPage,
  };
}
