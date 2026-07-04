import { useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME, REFETCH_DASHBOARD } from '../../constants/dashboard.constants';

export function useMinhasOSVencendoQuery() {
  return useQuery({
    queryKey: dashboardKeys.minhasOSVencendo(),
    queryFn: () => dashboardService.getMinhasOSVencendo(),
    staleTime: DASHBOARD_STALE_TIME,
    refetchInterval: REFETCH_DASHBOARD,
  });
}
