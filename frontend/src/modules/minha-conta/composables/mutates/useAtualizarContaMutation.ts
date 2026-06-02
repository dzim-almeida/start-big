import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { AxiosError } from 'axios';

import type { ApiError } from '@/shared/types/axios.types';
import type { UserResponse } from '@/shared/types/auth.types';
import type { AtualizarContaPayload } from '../../services/minhaConta.service';
import { atualizarConta } from '../../services/minhaConta.service';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

export function useAtualizarContaMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<UserResponse, AxiosError<ApiError>, AtualizarContaPayload>({
    mutationFn: atualizarConta,
    onSuccess: () => {
      toast.success('Dados atualizados com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['user-me'] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar dados') as string);
    },
  });
}
