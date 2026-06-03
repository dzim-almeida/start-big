import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { orcamentoService } from '../../orcamento.service';
import { orcamentoKeys, saleKeys } from '../../query.keys';

import { SaleRead } from '../../schemas/sale.schema';
import { ConverterOrcamento } from '../../schemas/orcamento.schema';

export function useConverterOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<SaleRead, AxiosError<ApiError>, { orcamentoId: number; payload: ConverterOrcamento }>({
    mutationFn: (variables) => orcamentoService.converterOrcamento(variables.orcamentoId, variables.payload),

    onSuccess: (createdSale) => {
      toast.success('Orçamento convertido em venda');

      queryClient.setQueryData(saleKeys.draft(createdSale.id), createdSale);

      queryClient.invalidateQueries({ queryKey: orcamentoKeys.lists() });
      queryClient.invalidateQueries({ queryKey: orcamentoKeys.status() });
      queryClient.invalidateQueries({ queryKey: saleKeys.lists() });
      queryClient.invalidateQueries({ queryKey: saleKeys.status() });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao converter orçamento'));
    },
  });
}
