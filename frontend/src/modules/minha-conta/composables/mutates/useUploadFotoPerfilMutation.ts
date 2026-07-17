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
    onSuccess: (usuarioAtualizado) => {
      toast.success('Foto atualizada com sucesso!');
      // A própria resposta do upload traz o url_perfil novo (UsuarioRead).
      // Escrevemos direto no cache em vez de invalidar: o refetch do GET /me
      // volta do cache do webview com a foto antiga, e só um reload manual
      // (que fura o cache) atualizava. setQueryData evita a rede por completo.
      queryClient.setQueryData(['user-me'], usuarioAtualizado);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar foto') as string);
    },
  });
}
