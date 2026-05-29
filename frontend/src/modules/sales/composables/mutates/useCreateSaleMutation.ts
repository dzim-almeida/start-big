import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SaleCreate, SaleRead } from '../../schemas/sale.schema';

export function useCreateSaleMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<SaleRead, AxiosError<ApiError>, SaleCreate>({
    mutationFn: saleService.createSale,

    onSuccess: (createdSale) => {
      queryClient.setQueryData(saleKeys.draft(createdSale.id), createdSale);
      queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: saleKeys.status(),
      });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao criar venda'));
    },
  });
}
