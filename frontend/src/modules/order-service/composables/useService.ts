import { computed, ref, watch } from 'vue';
import { refDebounced } from '@vueuse/core';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';

import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage, getConflictErrors, isConflictError } from '@/shared/utils/error.utils';

import type { ApiError } from '@/shared/types/axios.types';

import {
  createServico,
  getServicos,
  toggleServicoAtivo,
  updateServico,
} from '../services/servicos.service';
import { SERVICOS_QUERY_KEY, SERVICOS_STALE_TIME } from '../constants/servicos.constants';

import type {
  ServiceCreateZod,
  ServiceUpdateZod,
  ServiceReadZod,
} from '../schemas/servicos.schema';
import type { QueryParams } from '../types/servicos.types';

import type { StatusFilter } from '../types/servicos.types';

export function useService() {
  const searchQuery = ref<string | undefined>(undefined);
  const debouncedSearchQuery = refDebounced(searchQuery, 1000);
  const activeFilterQuery = ref<StatusFilter | null>(null)

  const filterQuery = computed<boolean | undefined>(() => {
    if (activeFilterQuery.value === 'ativos') return true
    if (activeFilterQuery.value === 'inativos') return false
    return
  })

  function useCreateServicoMutation(setErrors?: any) {
    const toast = useToast();
    const queryClient = useQueryClient();

    return useMutation<ServiceReadZod, AxiosError<ApiError>, ServiceCreateZod>({
      mutationFn: createServico,
      onSuccess: () => {
        toast.success('Serviço cadastrado com sucesso!');
        queryClient.invalidateQueries({ queryKey: [SERVICOS_QUERY_KEY] });
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

  function useUpdateServicoMutation(setErrors?: any) {
    const toast = useToast();
    const queryClient = useQueryClient();

    return useMutation<
      ServiceReadZod,
      AxiosError<ApiError>,
      { id: number; data: ServiceUpdateZod }
    >({
      mutationFn: ({ id, data }) => updateServico(id, data),
      onSuccess: () => {
        toast.success('Serviço atualizado com sucesso!');
        queryClient.invalidateQueries({ queryKey: [SERVICOS_QUERY_KEY] });
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

  function useToggleServicoAtivoMutation() {
    const toast = useToast();
    const queryClient = useQueryClient();

    return useMutation<ServiceReadZod, AxiosError<ApiError>, number>({
      mutationFn: toggleServicoAtivo,
      onSuccess: (data) => {
        const status = data.ativo ? 'ativado' : 'desativado';
        toast.success(`Serviço ${status} com sucesso!`);
        queryClient.invalidateQueries({ queryKey: [SERVICOS_QUERY_KEY] });
      },
      onError: (error) => {
        toast.error(getErrorMessage(error, 'Erro ao alterar status do serviço') as string);
      },
    });
  }

  function useServicesQuery(params?: QueryParams) {
  const query = useQuery({
    // Importante: debouncedSearchQuery.value aqui garante que a query
    // mude sempre que o usuário parar de digitar
    queryKey: [SERVICOS_QUERY_KEY, debouncedSearchQuery, filterQuery], 
    queryFn: () => getServicos({ search: debouncedSearchQuery.value, active: filterQuery.value,  ...params }),
    staleTime: SERVICOS_STALE_TIME,
  });

  // Usamos computed para que 'services' continue reagindo a mudanças no data do useQuery
  const services = computed(() => query.data.value?.items ?? []);

  watch(query.data, () => {
    console.log(query.data.value?.items)
  })

  return {
    services,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch
  };
}

  return {

    //Refs
    searchQuery,
    activeFilterQuery,

    // Métodos
    useCreateServicoMutation,
    useUpdateServicoMutation,
    useToggleServicoAtivoMutation,
    useServicesQuery
  }
}
