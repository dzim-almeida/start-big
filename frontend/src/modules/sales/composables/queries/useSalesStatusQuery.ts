import { useQuery } from '@tanstack/vue-query';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SalesStatus } from '../../schemas/sale.schema';

export function useSalesStatusQuery() {
  return useQuery<SalesStatus>({
    queryKey: saleKeys.status(),
    queryFn: () => saleService.getSalesStatus(),
    staleTime: 1000 * 60 * 30,
  });
}
