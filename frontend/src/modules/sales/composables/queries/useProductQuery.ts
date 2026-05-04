import { computed, unref, type MaybeRef } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { productService } from '../../api.service';
import { productKeys } from '../../query.keys';

import { ProductSaleListItem } from '../../schemas/productSale.schema';

export function useProductSearchQuery(term: MaybeRef<string | null | undefined>) {
  return useQuery<ProductSaleListItem>({
    queryKey: computed(() => 
      !!unref(term)
        ? productKeys.search(unref(term)!)
        : [...productKeys.all, 'search', 'empty']
    ),
    queryFn: () => productService.searchProducts(unref(term)!),
    enabled: computed(() => !!unref(term) && unref(term)!.trim().length >= 2),
    staleTime: 1000 * 30,
  });
}
