/**
 * useOSFormMutations - Mutations isoladas para operacoes de OS
 * Separado do useOSForm para melhor testabilidade e SRP
 */
import { computed } from 'vue';
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import type {
  OrdemServicoCreate,
  OrdemServicoRead,
  OrdemServicoUpdate,
} from '../types/ordemServico.types';
import type { ApiError } from '@/shared/types/axios.types';

import { ordemServicoService } from '../services/ordemServico.service';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';

export interface MutationCallbacks {
  onSuccess?: (data: OrdemServicoRead) => void;
  onError?: (message: string) => void;
}

export interface UseOSFormMutationsReturn {
  createMutation: ReturnType<typeof useMutation<OrdemServicoRead, AxiosError<ApiError>, OrdemServicoCreate>>;
  updateMutation: ReturnType<typeof useMutation<OrdemServicoRead, AxiosError<ApiError>, { id: number; data: OrdemServicoUpdate }>>;
  reopenMutation: ReturnType<typeof useMutation<OrdemServicoRead, AxiosError<ApiError>, number>>;
  isPending: ReturnType<typeof computed<boolean>>;
  createOS: (data: OrdemServicoCreate) => void;
  updateOS: (id: number, data: OrdemServicoUpdate) => void;
  reopenOS: (id: number) => void;
}

/**
 * Composable para mutations de Ordem de Servico
 */
export function useOSFormMutations(callbacks: MutationCallbacks = {}): UseOSFormMutationsReturn {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { onSuccess, onError } = callbacks;

  // Invalidate all OS-related queries
  function invalidateOSQueries() {
    queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });
    queryClient.invalidateQueries({ queryKey: ['os-estatisticas'] });
  }

  // Create Mutation
  const createMutation = useMutation<OrdemServicoRead, AxiosError<ApiError>, OrdemServicoCreate>({
    mutationFn: (data) => ordemServicoService.create(data),
    onSuccess: (data) => {
      toast.success('Ordem de Servico criada com sucesso!');
      invalidateOSQueries();
      onSuccess?.(data);
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Erro ao criar ordem de servico');
      onError?.(message);
    },
  });

  // Update Mutation
  const updateMutation = useMutation<
    OrdemServicoRead,
    AxiosError<ApiError>,
    { id: number; data: OrdemServicoUpdate }
  >({
    mutationFn: ({ id, data }) => ordemServicoService.update(id, data),
    onSuccess: (data) => {
      toast.success('Ordem de Servico atualizada com sucesso!');
      invalidateOSQueries();
      onSuccess?.(data);
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Erro ao atualizar ordem de servico');
      onError?.(message);
    },
  });

  // Reopen Mutation
  const reopenMutation = useMutation<OrdemServicoRead, AxiosError<ApiError>, number>({
    mutationFn: (id: number) => ordemServicoService.reabrir(id),
    onSuccess: (data) => {
      toast.success('Ordem de Servico reaberta com sucesso!');
      invalidateOSQueries();
      onSuccess?.(data);
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Erro ao reabrir ordem de servico');
      onError?.(message);
    },
  });

  // Combined pending state
  const isPending = computed(() => {
    return (
      createMutation.isPending.value ||
      updateMutation.isPending.value ||
      reopenMutation.isPending.value
    );
  });

  // Helper functions
  function createOS(data: OrdemServicoCreate) {
    createMutation.mutate(data);
  }

  function updateOS(id: number, data: OrdemServicoUpdate) {
    updateMutation.mutate({ id, data });
  }

  function reopenOS(id: number) {
    reopenMutation.mutate(id);
  }

  return {
    createMutation,
    updateMutation,
    reopenMutation,
    isPending,
    createOS,
    updateOS,
    reopenOS,
  };
}
