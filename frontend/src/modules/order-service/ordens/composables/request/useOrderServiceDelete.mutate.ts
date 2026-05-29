import { useMutation, useQueryClient } from '@tanstack/vue-query';

import { useToast } from '@/shared/composables/useToast';
import { AxiosError } from 'axios';
import { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';

import { deleteItemOS } from '../../services/orderServiceDelete.service';

import { OsDeleteItem } from '../../types/requests.type';

import { ORDER_SERVICE_QUERY_KEY } from '../../constants/core.constant';

export function useOrderServiceDeleteItem() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<void, AxiosError<ApiError>, OsDeleteItem>({
    mutationFn: deleteItemOS,
    onSuccess: () => {
      toast.success('Item excluído com sucesso');
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao excluir item') as string);
    },
  });
}
