/**
 * @fileoverview TanStack Query composable for cargos
 * @description Manages cargo listing with search and caching
 */

import { computed, type Ref } from 'vue';
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { getCargos, createCargo, updateCargo, deleteCargo } from '../services/position.service';
import type { CargoCreate, CargoRead, CargoUpdate } from '../types/positions.types';
import type { ApiError } from '@/shared/types/axios.types';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage, getConflictErrors, isConflictError } from '@/shared/utils/error.utils';

const QUERY_KEY = 'cargos';
const STALE_TIME = 1000 * 60 * 5; // 5 minutes

/**
 * Query for listing cargos
 * @param searchTerm - Optional reactive search term
 */
export function usePositionsQuery(searchTerm?: Ref<string>) {
  const cleanSearch = computed(() => searchTerm?.value?.trim() || undefined);

  return useQuery({
    queryKey: [QUERY_KEY, cleanSearch],
    queryFn: () => getCargos(cleanSearch.value),
    staleTime: STALE_TIME,
  });
}

/**
 * Mutation for creating cargo
 */
export function useCreatePositionMutation(setErrors?: (errors: Record<string, string>) => void) {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<CargoRead, AxiosError<ApiError>, CargoCreate>({
    mutationFn: createCargo,
    onSuccess: () => {
      toast.success('Cargo criado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
    onError: (error) => {
      if (isConflictError(error)) {
        const conflictedErrors = getConflictErrors(error);
        if (conflictedErrors && setErrors) {
          setErrors(conflictedErrors);
          toast.error('Erro ao criar cargo', 'Nome ja registrado');
          return;
        }
      }
      toast.error(getErrorMessage(error, 'Erro ao criar cargo') as string);
    },
  });
}

/**
 * Mutation for updating cargo
 */
export function useUpdatePositionMutation(setErrors?: (errors: Record<string, string>) => void) {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<
    CargoRead,
    AxiosError<ApiError>,
    { id: number; data: CargoUpdate }
  >({
    mutationFn: ({ id, data }) => updateCargo(id, data),
    onSuccess: () => {
      toast.success('Cargo atualizado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
    onError: (error) => {
      if (isConflictError(error)) {
        const conflictedErrors = getConflictErrors(error);
        if (conflictedErrors && setErrors) {
          setErrors(conflictedErrors);
          toast.error('Erro ao atualizar cargo', 'Nome ja registrado');
          return;
        }
      }
      toast.error(getErrorMessage(error, 'Erro ao atualizar cargo') as string);
    },
  });
}

/**
 * Mutation for deleting cargo
 */
export function useDeletePositionMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<void, AxiosError<ApiError>, number>({
    mutationFn: deleteCargo,
    onSuccess: () => {
      toast.success('Cargo removido com sucesso!');
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao remover cargo') as string);
    },
  });
}
