import { type MaybeRef, unref, computed } from 'vue';

import { useQuery } from '@tanstack/vue-query';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SaleRead } from '../../schemas/sale.schema';

export function useSaleDraftQuery(saleId: MaybeRef<number | null | undefined>) {
  return useQuery<SaleRead>({
    queryKey: computed(() =>
      !!unref(saleId)
        ? saleKeys.draft(unref(saleId)!)
        : ([...saleKeys.all, 'draft', 'empty'] as const),
    ),

    queryFn: () => saleService.getSale(unref(saleId)!),
    enabled: computed(() => !!unref(saleId)),
    staleTime: 1000 * 15, // 15 seconds
  });
}
