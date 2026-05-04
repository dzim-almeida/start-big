import { useMutation, useQueryClient } from '@tanstack/vue-query';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SaleCreate, SaleRead } from '../../schemas/sale.schema';

export function useCreateSaleMutation() {
  const queryClient = useQueryClient();

  return useMutation<SaleRead, Error, SaleCreate>({
    mutationFn: saleService.createSale,

    onSuccess: (createdSale) => {
      queryClient.setQueryData(saleKeys.draft(createdSale.id), createdSale);
      queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
      });
    },

    onError: (error) => {
      console.error('[useCreateSaleMutation] Error creating sale:', error);
    },
  });
}
