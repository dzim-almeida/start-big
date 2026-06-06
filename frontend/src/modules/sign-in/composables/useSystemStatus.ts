import { useQuery } from '@tanstack/vue-query';
import { checkSystemStatus } from '../services/sign-in.service';

/**
 * Composable para verificar se o sistema foi inicializado
 */
export function useSystemStatusQuery() {
  return useQuery({
    queryKey: ['system-status'],
    queryFn: checkSystemStatus,
    staleTime: 1000 * 60 * 5, // 5 minutos
    retry: 1,
  });
}
