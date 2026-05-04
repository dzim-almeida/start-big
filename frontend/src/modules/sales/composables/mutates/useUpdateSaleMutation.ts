import { useMutation, useQueryClient } from '@tanstack/vue-query';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SaleUpdate, SaleRead } from '../../schemas/sale.schema';

export function useUpdateSaleMutation() {
  const queryClient = useQueryClient();

  return useMutation<SaleRead, Error, { saleId: number; payload: SaleUpdate }>({
    mutationFn: (variables) => saleService.updateSale(variables.saleId, variables.payload),

    onSuccess: (updatedSale) => {
      queryClient.setQueryData(saleKeys.draft(updatedSale.id), updatedSale);
    },

    onError: (error) => {
      console.error('[useUpdateSaleMutation] Error updating sale:', error);
    },
  });
}
