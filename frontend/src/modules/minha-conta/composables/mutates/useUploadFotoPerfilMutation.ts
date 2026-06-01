import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { AxiosError } from 'axios';

import type { ApiError } from '@/shared/types/axios.types';
import type { UserResponse } from '@/shared/types/auth.types';
import { uploadFotoPerfil } from '../../services/minhaConta.service';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

export function useUploadFotoPerfilMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<UserResponse, AxiosError<ApiError>, File>({
    mutationFn: uploadFotoPerfil,
    onSuccess: () => {
      toast.success('Foto atualizada com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['user-me'] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar foto') as string);
    },
  });
}
