import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { AxiosError } from 'axios';

import { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';

import {
  updateOrderService,
  updateEquipOS,
  updateItemOS,
  updateReadyOS,
  updateCancelOS,
  updateReopen,
} from '../../services/orderServiceUpdate.service';

import { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';

import {
  OrderServiceUpdateRequest,
  OsEquipUpdateRequest,
  OsItemUpdateRequest,
  OsReadyUpdateRequest,
  OsCancelUpdateRequest,
} from '../../types/requests.type';

import { ORDER_SERVICE_QUERY_KEY } from '../../constants/core.constant';

export function useUpdateOrderServiceMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, OrderServiceUpdateRequest>({
    mutationFn: updateOrderService,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} atualizada com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar a ordem de serviço') as string);
    },
  });
}

export function useUpdateEquipOSMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, OsEquipUpdateRequest>({
    mutationFn: updateEquipOS,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} equipamento atualizado com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar o equipamento') as string);
    },
  });
}

export function useUpdateItemOSMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, OsItemUpdateRequest>({
    mutationFn: updateItemOS,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} item atualizado com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar o item') as string);
    },
  });
}

export function useReadyOrderServiceMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, OsReadyUpdateRequest>({
    mutationFn: updateReadyOS,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} finalizada com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao finalizar a ordem de serviço') as string);
    },
  });
}

export function useCancelOrderServiceMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, OsCancelUpdateRequest>({
    mutationFn: updateCancelOS,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} cancelada com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao cancelar a ordem de serviço') as string);
    },
  });
}

export function useReopenOrderServiceMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<OrderServiceReadDataType, AxiosError<ApiError>, string>({
    mutationFn: updateReopen,
    onSuccess: (data) => {
      toast.success(`${data.numero_os} reaberta com sucesso`);
      queryClient.invalidateQueries({ queryKey: [ORDER_SERVICE_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao reabrir a ordem de serviço') as string);
    },
  });
}
