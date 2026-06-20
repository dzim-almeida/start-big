import { computed, unref, type MaybeRef } from 'vue';
import { keepPreviousData, useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';
import type { PeriodFilter } from '../../types/dashboard.types';

export function useRankingFuncionariosQuery(periodo: MaybeRef<PeriodFilter>) {
  return useQuery({
    queryKey: computed(() => dashboardKeys.rankingFuncionarios(unref(periodo))),
    queryFn: () => dashboardService.getRankingFuncionarios(unref(periodo)),
    staleTime: DASHBOARD_STALE_TIME,
    placeholderData: keepPreviousData,
  });
}
