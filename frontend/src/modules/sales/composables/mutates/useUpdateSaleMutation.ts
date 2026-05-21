import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

import { SaleUpdate, SaleRead } from '../../schemas/sale.schema';

export function useUpdateSaleMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<SaleRead, AxiosError<ApiError>, { saleId: number; payload: SaleUpdate }>({
    mutationFn: (variables) => saleService.updateSale(variables.saleId, variables.payload),

    onSuccess: (updatedSale) => {
      queryClient.setQueryData(saleKeys.draft(updatedSale.id), updatedSale);
      queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
      })
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar venda'));
    },
  });
}
