import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { orcamentoService } from '../../orcamento.service';
import { orcamentoKeys } from '../../query.keys';

import { OrcamentoCreate, OrcamentoRead } from '../../schemas/orcamento.schema';

export function useCreateOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<OrcamentoRead, AxiosError<ApiError>, OrcamentoCreate>({
    mutationFn: orcamentoService.createOrcamento,

    onSuccess: (createdOrcamento) => {
      queryClient.setQueryData(orcamentoKeys.draft(createdOrcamento.id), createdOrcamento);
      queryClient.invalidateQueries({
        queryKey: orcamentoKeys.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: orcamentoKeys.status(),
      });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao criar orçamento'));
    },
  });
}
