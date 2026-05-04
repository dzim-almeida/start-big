import { useMutation, useQueryClient } from '@tanstack/vue-query';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SaleRead } from '../../schemas/sale.schema';

export function useCancelSaleMutation() {
  const queryClient = useQueryClient();

  return useMutation<SaleRead, Error, { saleId: number }>({
    mutationFn: ({ saleId }) => saleService.cancelSale(saleId),
    onSuccess: (canceledSale) => {
      queryClient.invalidateQueries({
        queryKey: saleKeys.draft(canceledSale.id),
      });
      queryClient.setQueryData(saleKeys.detail(canceledSale.id), canceledSale);
      queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
      });
    },
  });
}
