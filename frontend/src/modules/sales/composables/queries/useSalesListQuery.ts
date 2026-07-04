import { type MaybeRef, unref, computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { SaleList, SaleSearch } from '../../schemas/sale.schema';
import { saleKeys } from '../../query.keys';
import { saleService } from '../../api.service';
import { REFETCH_REALTIME } from '@/core/config/queryIntervals';

export function useSalesListQuery(
  filters?: MaybeRef<SaleSearch | null | undefined>,
  page?: MaybeRef<number | null | undefined>,
) {
  return useQuery<SaleList>({
    queryKey: computed(() => 
      !!unref(filters)
        ? saleKeys.list(unref(filters) ?? undefined, unref(page) ?? 1)
        : saleKeys.list(undefined, unref(page) ?? 1)
    ),
    queryFn: () => saleService.listSales(unref(filters)!, unref(page)!),
    staleTime: 1000 * 30,
    refetchInterval: REFETCH_REALTIME,
  });
}
