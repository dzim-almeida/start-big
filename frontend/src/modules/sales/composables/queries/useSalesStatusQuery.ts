import { useQuery } from '@tanstack/vue-query';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';
import { REFETCH_REALTIME } from '@/core/config/queryIntervals';

import { SalesStatus } from '../../schemas/sale.schema';

export function useSalesStatusQuery() {
  return useQuery<SalesStatus>({
    queryKey: saleKeys.status(),
    queryFn: () => saleService.getSalesStatus(),
    staleTime: 1000 * 60 * 30,
    refetchInterval: REFETCH_REALTIME,
  });
}
