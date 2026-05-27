import { useQuery } from '@tanstack/vue-query';

import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys, DASHBOARD_STALE_TIME } from '../../constants/dashboard.constants';

export function useEstoqueBaixoQuery() {
  return useQuery({
    queryKey: dashboardKeys.estoqueBaixo(),
    queryFn: () => dashboardService.getEstoqueBaixo(),
    staleTime: DASHBOARD_STALE_TIME,
  });
}
