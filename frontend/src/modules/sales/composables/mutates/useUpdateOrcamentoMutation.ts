import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { orcamentoService } from '../../orcamento.service';
import { orcamentoKeys } from '../../query.keys';

import { OrcamentoUpdate, OrcamentoRead } from '../../schemas/orcamento.schema';

export function useUpdateOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<OrcamentoRead, AxiosError<ApiError>, { orcamentoId: number; payload: OrcamentoUpdate }>({
    mutationFn: (variables) => orcamentoService.updateOrcamento(variables.orcamentoId, variables.payload),

    onSuccess: (updatedOrcamento) => {
      queryClient.setQueryData(orcamentoKeys.draft(updatedOrcamento.id), updatedOrcamento);
      queryClient.invalidateQueries({
        queryKey: orcamentoKeys.lists(),
      });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar orçamento'));
    },
  });
}
