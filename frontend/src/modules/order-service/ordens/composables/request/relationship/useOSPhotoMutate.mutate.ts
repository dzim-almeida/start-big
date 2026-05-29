import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { AxiosError } from 'axios';

import { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';

import { uploadFotoOS, deleteFotoOS } from '../../../services/relationship/osPhotoMutate.service';

import { OsImageReadDataType } from '../../../schemas/relationship/osPhoto.schema';

import { OsFotoUploadRequest, OsFotoDeleteRequest } from '../../../types/requests.type';

import { ORDER_SERVICE_QUERY_KEY } from '../../../constants/core.constant';

export function useUploadFotoOSMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OsImageReadDataType, AxiosError<ApiError>, OsFotoUploadRequest>({
    mutationFn: uploadFotoOS,
    onSuccess: (data) => {
      toast.success(`Foto ${data.nome_arquivo} enviada com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao enviar foto') as string);
    },
  });
}

export function useDeleteFotoOSMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<void, AxiosError<ApiError>, OsFotoDeleteRequest>({
    mutationFn: deleteFotoOS,
    onSuccess: () => {
      toast.success('Foto excluída com sucesso');
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao excluir foto') as string);
    },
  });
}
