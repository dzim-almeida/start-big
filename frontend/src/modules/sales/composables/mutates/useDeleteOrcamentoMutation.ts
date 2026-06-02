import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { orcamentoService } from '../../orcamento.service';
import { orcamentoKeys } from '../../query.keys';

export function useDeleteOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<void, AxiosError<ApiError>, { orcamentoId: number }>({
    mutationFn: (variables) => orcamentoService.deleteOrcamento(variables.orcamentoId),

    onSuccess: () => {
      toast.success('Orçamento excluído');
      queryClient.invalidateQueries({
        queryKey: orcamentoKeys.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: orcamentoKeys.status(),
      });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao excluir orçamento'));
    },
  });
}
