import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import {
  getErrorMessage,
  getConflictErrors,
  isConflictError,
} from '@/shared/utils/error.utils';
import {
  createServico,
  toggleServicoAtivo,
  updateServico,
} from '../services/servicos.service';
import {
  SERVICOS_QUERY_KEY,
  SERVICOS_STATS_QUERY_KEY,
} from '../constants/servicos.constants';
import type { ServicoCreate, ServicoRead, ServicoUpdate } from '../types/servicos.types';

function invalidateServicoQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: [SERVICOS_QUERY_KEY] });
  queryClient.invalidateQueries({ queryKey: [SERVICOS_STATS_QUERY_KEY] });
}

export function useCreateServicoMutation(setErrors?: any) {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<ServicoRead, AxiosError<ApiError>, ServicoCreate>({
    mutationFn: createServico,
    onSuccess: () => {
      toast.success('Serviço cadastrado com sucesso!');
      invalidateServicoQueries(queryClient);
    },
    onError: (error) => {
      if (isConflictError(error) && setErrors) {
        const conflictErrors = getConflictErrors(error);
        if (conflictErrors) {
          setErrors(conflictErrors);
          toast.error('Erro ao cadastrar serviço', 'Dados já registrados');
          return;
        }
      }

      toast.error(getErrorMessage(error, 'Erro ao cadastrar serviço') as string);
    },
  });
}

export function useUpdateServicoMutation(setErrors?: any) {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    ServicoRead,
    AxiosError<ApiError>,
    { id: number; data: ServicoUpdate }
  >({
    mutationFn: ({ id, data }) => updateServico(id, data),
    onSuccess: () => {
      toast.success('Serviço atualizado com sucesso!');
      invalidateServicoQueries(queryClient);
    },
    onError: (error) => {
      if (isConflictError(error) && setErrors) {
        const conflictErrors = getConflictErrors(error);
        if (conflictErrors) {
          setErrors(conflictErrors);
          toast.error('Erro ao atualizar serviço', 'Dados já registrados');
          return;
        }
      }

      toast.error(getErrorMessage(error, 'Erro ao atualizar serviço') as string);
    },
  });
}

export function useToggleServicoAtivoMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<ServicoRead, AxiosError<ApiError>, number>({
    mutationFn: toggleServicoAtivo,
    onSuccess: (data) => {
      const status = data.ativo ? 'ativado' : 'desativado';
      toast.success(`Serviço ${status} com sucesso!`);
      invalidateServicoQueries(queryClient);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao alterar status do serviço') as string);
    },
  });
}

export function useServicoActions(setErrors?: any) {
  const createMutation = useCreateServicoMutation(setErrors);
  const updateMutation = useUpdateServicoMutation(setErrors);
  const toggleAtivoMutation = useToggleServicoAtivoMutation();

  return {
    createMutation,
    updateMutation,
    toggleAtivoMutation,
  };
}
