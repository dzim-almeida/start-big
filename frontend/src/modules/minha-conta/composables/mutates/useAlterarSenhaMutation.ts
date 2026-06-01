import { useMutation } from '@tanstack/vue-query';
import { AxiosError } from 'axios';

import type { ApiError } from '@/shared/types/axios.types';
import type { UserResponse } from '@/shared/types/auth.types';
import type { AlterarSenhaPayload } from '../../services/minhaConta.service';
import { alterarSenha } from '../../services/minhaConta.service';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

export function useAlterarSenhaMutation() {
  const toast = useToast();

  return useMutation<UserResponse, AxiosError<ApiError>, AlterarSenhaPayload>({
    mutationFn: alterarSenha,
    onSuccess: () => {
      toast.success('Senha alterada com sucesso!');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao alterar senha') as string);
    },
  });
}
