import { useQuery } from '@tanstack/vue-query';
import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useMinhasOSAtrasadasQuery() {
  return useQuery({
    queryKey: dashboardKeys.minhasOSAtrasadas(),
    queryFn: () => dashboardService.getMinhasOSAtrasadas(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
