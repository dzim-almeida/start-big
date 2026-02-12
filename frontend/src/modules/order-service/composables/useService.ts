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
  getServicosStats,
  toggleServicoAtivo,
  updateServico,
} from '../services/servicos.service';
import { SERVICOS_QUERY_KEY, SERVICOS_STATS_QUERY_KEY, SERVICOS_STALE_TIME } from '../constants/servicos.constants';

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
  const currentPage = ref(1);

  const filterQuery = computed<boolean | undefined>(() => {
    if (activeFilterQuery.value === 'ativos') return true
    if (activeFilterQuery.value === 'inativos') return false
    return
  })

  function setPage(page: number) {
    currentPage.value = page;
  }

  // Resetar pagina ao mudar filtros
  watch([debouncedSearchQuery, filterQuery], () => {
    currentPage.value = 1;
  });

  function useCreateServicoMutation(setErrors?: any) {
    const toast = useToast();
    const queryClient = useQueryClient();

    return useMutation<ServiceReadZod, AxiosError<ApiError>, ServiceCreateZod>({
      mutationFn: createServico,
      onSuccess: () => {
        toast.success('Serviço cadastrado com sucesso!');
        queryClient.invalidateQueries({ queryKey: [SERVICOS_QUERY_KEY] });
        queryClient.invalidateQueries({ queryKey: [SERVICOS_STATS_QUERY_KEY] });
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
        queryClient.invalidateQueries({ queryKey: [SERVICOS_STATS_QUERY_KEY] });
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
        queryClient.invalidateQueries({ queryKey: [SERVICOS_STATS_QUERY_KEY] });
      },
      onError: (error) => {
        toast.error(getErrorMessage(error, 'Erro ao alterar status do serviço') as string);
      },
    });
  }

  function useServicosStatsQuery() {
    const query = useQuery({
      queryKey: [SERVICOS_STATS_QUERY_KEY],
      queryFn: getServicosStats,
      staleTime: SERVICOS_STALE_TIME,
    });

    const stats = computed(() => ({
      total: query.data.value?.total ?? 0,
      ativos: query.data.value?.ativos ?? 0,
      inativos: query.data.value?.inativos ?? 0,
      mediaValor: query.data.value?.media_valor ?? 0,
    }));

    return {
      stats,
      isLoading: query.isLoading,
    };
  }

  function useServicesQuery(params?: QueryParams) {
    const query = useQuery({
      queryKey: [SERVICOS_QUERY_KEY, debouncedSearchQuery, filterQuery, currentPage],
      queryFn: () => getServicos({
        search: debouncedSearchQuery.value,
        active: filterQuery.value,
        page: currentPage.value,
        ...params,
      }),
      staleTime: SERVICOS_STALE_TIME,
    });

    const services = computed(() => query.data.value?.items ?? []);
    const totalPages = computed(() => query.data.value?.total_pages ?? 1);
    const totalItems = computed(() => query.data.value?.total_items ?? 0);

    return {
      services,
      totalPages,
      totalItems,
      isLoading: query.isLoading,
      isError: query.isError,
      error: query.error,
      refetch: query.refetch,
    };
  }

  return {

    // Refs
    searchQuery,
    activeFilterQuery,
    currentPage,

    // Métodos
    setPage,
    useCreateServicoMutation,
    useUpdateServicoMutation,
    useToggleServicoAtivoMutation,
    useServicesQuery,
    useServicosStatsQuery
  }
}
