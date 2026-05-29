import { computed, unref, type MaybeRef } from 'vue';
import { keepPreviousData, useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';
import type { PeriodFilter } from '../../types/dashboard.types';

export function useDashboardStatsQuery(periodo: MaybeRef<PeriodFilter>) {
  return useQuery({
    queryKey: computed(() => dashboardKeys.stats(unref(periodo))),
    queryFn: () => dashboardService.getStats(unref(periodo)),
    staleTime: DASHBOARD_STALE_TIME,
    placeholderData: keepPreviousData,
  });
}
