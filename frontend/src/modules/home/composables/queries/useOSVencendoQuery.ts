import { useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useOSVencendoQuery() {
  return useQuery({
    queryKey: dashboardKeys.osVencendo(),
    queryFn: () => dashboardService.getOSVencendo(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
