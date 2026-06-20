import { useQuery } from '@tanstack/vue-query';
import { dashboardService } from '../../services/dashboard.service';
import { dashboardKeys } from '../../constants/dashboard.constants';

export function useMinhaAtividadeHojeQuery() {
  return useQuery({
    queryKey: dashboardKeys.minhaAtividadeHoje(),
    queryFn: () => dashboardService.getMinhaAtividadeHoje(),
    staleTime: 1000 * 30, // 30s — atividade muda com frequência
  });
}
