import { useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME, REFETCH_DASHBOARD } from '../../constants/dashboard.constants';

export function useUltimasVendasQuery() {
  return useQuery({
    queryKey: dashboardKeys.ultimasVendas(),
    queryFn: () => dashboardService.getUltimasVendas(),
    staleTime: DASHBOARD_STALE_TIME,
    refetchInterval: REFETCH_DASHBOARD,
  });
}
