import { computed, unref, type MaybeRef } from 'vue';

import { useQuery } from '@tanstack/vue-query';

import { saleKeys } from '../../query.keys';
import { saleService } from '../../api.service';
import { REFETCH_REALTIME } from '@/core/config/queryIntervals';

import { SaleRead } from '../../schemas/sale.schema';

export function useSaleDetailQuery(saleId: MaybeRef<number | null | undefined>) {
  return useQuery<SaleRead>({
    queryKey: computed(() =>
      !!unref(saleId)
        ? saleKeys.detail(unref(saleId)!)
        : ([...saleKeys.all, 'detail', 'empty'] as const),
    ),
    queryFn: () => saleService.getSale(unref(saleId)!),
    enabled: computed(() => !!unref(saleId)),
    staleTime: 1000 * 60 * 5,
    refetchInterval: REFETCH_REALTIME,
  });
}
