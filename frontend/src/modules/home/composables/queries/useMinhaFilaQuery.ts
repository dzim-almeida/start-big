import { useQuery } from '@tanstack/vue-query';
import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useMinhaFilaQuery() {
  return useQuery({
    queryKey: dashboardKeys.minhaFila(),
    queryFn: () => dashboardService.getMinhaFila(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
