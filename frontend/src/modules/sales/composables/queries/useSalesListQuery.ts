import { useQuery } from '@tanstack/vue-query';
import { SaleList, SaleSearch } from '../../schemas/sale.schema';
import { saleKeys } from '../../query.keys';
import { saleService } from '../../api.service';

export function useSalesListQuery(filters?: SaleSearch) {
  return useQuery<SaleList>({
    queryKey: saleKeys.list(filters),
    queryFn: () => saleService.listSales(filters),
    staleTime: 1000 * 30, // 30 seconds
  });
}
