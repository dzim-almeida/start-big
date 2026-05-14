import { useMutation, useQueryClient } from '@tanstack/vue-query';

import { saleService } from '../../api.service';

import {
  ProductSaleCreate,
  ProductSaleUpdate,
  ProductAlteration,
} from '../../schemas/productSale.schema';

import { patchDraftCache } from '../../updateDraftCache.helper';
import { saleKeys } from '../../query.keys';
import { SaleRead } from '../../schemas/sale.schema';

export function useAddItemSaleMutation() {
  const queryClient = useQueryClient();

  return useMutation<ProductAlteration, Error, { saleId: number; payload: ProductSaleCreate }>({
    mutationFn: (variables) => saleService.addItemInSale(variables.saleId, variables.payload),

    onSuccess: (response, { saleId }) => {
      patchDraftCache(queryClient, saleId, response);
    },

    onError: (error) => {
      console.error('[useAddItemSaleMutation] Error adding item to sale:', error);
    },
  });
}

export function useUpdateItemSaleMutation() {
  const queryClient = useQueryClient();

  return useMutation<
    ProductAlteration,
    Error,
    { saleId: number; productId: number; payload: ProductSaleUpdate }
  >({
    mutationFn: (variables) =>
      saleService.updateItemInSale(variables.saleId, variables.productId, variables.payload),

    onSuccess: (response, { saleId }) => {
      patchDraftCache(queryClient, saleId, response);
    },

    onError: (error) => {
      console.error('[useItemSaleMutation] Error updating item in sale:', error);
    },
  });
}

export function useDeleteItemSaleMutation() {
  const queryClient = useQueryClient();

  return useMutation<SaleRead, Error, { saleId: number; productId: number }>({
    mutationFn: (variables) => saleService.deleteItemInSale(variables.saleId, variables.productId),

    onSuccess: (updatedSale, { saleId }) => {
      queryClient.setQueryData(saleKeys.draft(saleId), updatedSale);
      queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
      });
    },
    
    onError: (error) => {
      console.error('[useItemSaleMutation] Error deleting item from sale:', error);
    },
  });
}
