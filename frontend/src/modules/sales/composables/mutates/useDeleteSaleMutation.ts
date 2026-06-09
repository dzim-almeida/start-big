import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { saleService } from '../../api.service';
import { saleKeys } from '../../query.keys';

export function useDeleteSaleMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<void, AxiosError<ApiError>, { saleId: number }>({
    mutationFn: ({ saleId }) => saleService.deleteSale(saleId),
    onSuccess: (_, { saleId }) => {
      toast.success('Venda descartada');
      queryClient.invalidateQueries({ queryKey: saleKeys.draft(saleId) });
      queryClient.invalidateQueries({ queryKey: saleKeys.lists() });
      queryClient.invalidateQueries({ queryKey: saleKeys.status() });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao descartar venda'));
    },
  });
}
