import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';

import { updateCustomer, toggleCustomerAtivo } from '../../services/customerUpdate.service';

import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';
import type { CustomerUpdateDataType } from '../../schemas/customerMutate.schema';

import { CUSTOMER_QUERY_KEY } from '../../constants/customer.constant';

// ── Update ─────────────────────────────────────────────────────────────────

interface UpdateCustomerRequest {
  id: number;
  data: CustomerUpdateDataType;
}

export function useUpdateCustomerMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    CustomerUnionReadSchemaDataType,
    AxiosError<ApiError>,
    UpdateCustomerRequest
  >({
    mutationFn: ({ id, data }) => updateCustomer(id, data),
    onSuccess: () => {
      toast.success('Cliente atualizado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [CUSTOMER_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar cliente') as string);
    },
  });
}

// ── Toggle Ativo ───────────────────────────────────────────────────────────

export function useToggleCustomerAtivoMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    CustomerUnionReadSchemaDataType,
    AxiosError<ApiError>,
    number
  >({
    mutationFn: toggleCustomerAtivo,
    onSuccess: (data) => {
      const status = data.ativo ? 'ativado' : 'desativado';
      toast.success(`Cliente ${status} com sucesso!`);
      queryClient.invalidateQueries({ queryKey: [CUSTOMER_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao alterar status do cliente') as string);
    },
  });
}
