import { useQuery } from '@tanstack/vue-query';
import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useOSPorStatusQuery() {
  return useQuery({
    queryKey: dashboardKeys.osPorStatus(),
    queryFn: () => dashboardService.getOSPorStatus(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
