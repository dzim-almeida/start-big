import { useQuery } from '@tanstack/vue-query';
import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME, REFETCH_DASHBOARD } from '../../constants/dashboard.constants';

export function useOSAtrasadasEmpresaQuery() {
  return useQuery({
    queryKey: dashboardKeys.osAtrasadasEmpresa(),
    queryFn: () => dashboardService.getOSAtrasadasEmpresa(),
    staleTime: DASHBOARD_STALE_TIME,
    refetchInterval: REFETCH_DASHBOARD,
  });
}
