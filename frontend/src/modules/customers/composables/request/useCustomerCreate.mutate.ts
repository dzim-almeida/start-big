import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import type { ApiError } from '@/shared/types/axios.types';
import { useToast } from '@/shared/composables/useToast';

import { createCustomerPF, createCustomerPJ } from '../../services/customerCreate.service';

import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';
import type { CustomerPFCreateDataType, CustomerPJCreateDataType } from '../../schemas/customerMutate.schema';

import { CUSTOMER_QUERY_KEY } from '../../constants/customer.constant';

export function useCreateCustomerPFMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    CustomerUnionReadSchemaDataType,
    AxiosError<ApiError>,
    CustomerPFCreateDataType
  >({
    mutationFn: createCustomerPF,
    onSuccess: () => {
      toast.success('Cliente PF cadastrado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [CUSTOMER_QUERY_KEY] });
    },
  });
}

export function useCreateCustomerPJMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    CustomerUnionReadSchemaDataType,
    AxiosError<ApiError>,
    CustomerPJCreateDataType
  >({
    mutationFn: createCustomerPJ,
    onSuccess: () => {
      toast.success('Cliente PJ cadastrado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [CUSTOMER_QUERY_KEY] });
    },
  });
}
