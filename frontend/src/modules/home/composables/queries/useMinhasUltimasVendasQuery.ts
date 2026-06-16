import { useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useMinhasUltimasVendasQuery() {
  return useQuery({
    queryKey: dashboardKeys.minhasUltimasVendas(),
    queryFn: () => dashboardService.getMinhasUltimasVendas(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
