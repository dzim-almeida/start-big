import { computed, unref, type MaybeRef } from 'vue';

import { useQuery } from '@tanstack/vue-query';

import { saleKeys } from '../../sales.keys';
import { saleService } from '../../sales.service';

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
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
