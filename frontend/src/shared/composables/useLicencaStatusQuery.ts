import { useQuery } from '@tanstack/vue-query';
import { verificarLicenca } from '@/shared/services/licenca.service';

export function useLicencaStatusQuery() {
  return useQuery({
    queryKey: ['licenca-status'],
    queryFn: verificarLicenca,
    staleTime: 1000 * 60 * 5, // 5 minutos (alinhado com o throttle do router)
    retry: false,
    refetchOnWindowFocus: false,
  });
}
