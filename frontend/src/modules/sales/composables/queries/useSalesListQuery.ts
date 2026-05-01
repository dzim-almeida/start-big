import { useQuery } from '@tanstack/vue-query';
import { SaleList, SaleSearch } from '../../schemas/sale.schema';
import { saleKeys } from '../../sales.keys';
import { saleService } from '../../sales.service';

export function useSalesListQuery(filters?: SaleSearch) {
  return useQuery<SaleList>({
    queryKey: saleKeys.list(filters),
    queryFn: () => saleService.listSales(filters),
    staleTime: 1000 * 30, // 30 seconds
  });
}
