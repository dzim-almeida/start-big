import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { AxiosError } from 'axios';

import { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';
import {
  ORDER_SERVICE_QUERY_KEY,
  ORDER_SERVICE_STATS_QUERY_KEY,
} from '../../constants/core.constant';

import { createOrderService } from '../../services/orderServiceCreate.service';
import { createItemOS } from '../../services/orderServiceCreate.service';

import { OrderServiceCreateSchemaDataType } from '../../schemas/orderServiceMutate.schema';
import { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';

import { OsItemCreateRequest } from '../../types/requests.type';

export function useCreateOrderServiceMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    OrderServiceReadDataType,
    AxiosError<ApiError>,
    OrderServiceCreateSchemaDataType
  >({
    mutationFn: createOrderService,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} cadastrada com sucesso!`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_STATS_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao cadastrar ordem de serviço') as string);
    },
  });
}

export function useCreateItemOSMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, OsItemCreateRequest>({
    mutationFn: createItemOS,
    onSuccess: (data) => {
      const lastItem = data.itens.at(-1);
      const itemType = lastItem?.tipo === 'PRODUTO' ? 'Produto' : 'Serviço';
      toast.success(`${itemType} adicionado com sucesso na ${data.numero_os}`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao adicionar item na ordem de serviço') as string);
    },
  });
}
