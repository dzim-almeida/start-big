import { useQuery } from '@tanstack/vue-query';
import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useOSAguardandoRetiradaQuery() {
  return useQuery({
    queryKey: dashboardKeys.osAguardandoRetirada(),
    queryFn: () => dashboardService.getOSAguardandoRetirada(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
