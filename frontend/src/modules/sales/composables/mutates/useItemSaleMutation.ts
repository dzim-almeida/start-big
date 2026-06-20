import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { saleService } from '../../api.service';

import {
  ProductSaleCreate,
  ProductSaleUpdate,
  ProductAlteration,
} from '../../schemas/productSale.schema';

import { patchDraftCache } from '../../updateDraftCache.helper';
import { saleKeys } from '../../query.keys';
import { SaleRead } from '../../schemas/sale.schema';

export function useAddItemSaleMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<ProductAlteration, AxiosError<ApiError>, { saleId: number; payload: ProductSaleCreate }>({
    mutationFn: (variables) => saleService.addItemInSale(variables.saleId, variables.payload),

    onSuccess: (response, { saleId }) => {
      toast.success('Produto adicionado');
      patchDraftCache(queryClient, saleId, response);
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao adicionar produto'));
    },
  });
}

export function useUpdateItemSaleMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<
    ProductAlteration,
    AxiosError<ApiError>,
    { saleId: number; productId: number; payload: ProductSaleUpdate }
  >({
    mutationFn: (variables) =>
      saleService.updateItemInSale(variables.saleId, variables.productId, variables.payload),

    onSuccess: (response, { saleId }) => {
      toast.success('Item atualizado');
      patchDraftCache(queryClient, saleId, response);
    },

    onError: (error) => {
      const detail = (error?.response?.data as any)?.detail;
      if (['REQUER_APROVACAO_GERENTE', 'PIN_GERENTE_INVALIDO'].includes(detail)) return;
      toast.error(getErrorMessage(error, 'Erro ao atualizar item'));
    },
  });
}

export function useDeleteItemSaleMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<SaleRead, AxiosError<ApiError>, { saleId: number; productId: number }>({
    mutationFn: (variables) => saleService.deleteItemInSale(variables.saleId, variables.productId),

    onSuccess: (updatedSale, { saleId }) => {
      toast.success('Item removido');
      queryClient.setQueryData(saleKeys.draft(saleId), updatedSale);
      queryClient.invalidateQueries({
        queryKey: saleKeys.lists(),
      });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao remover item'));
    },
  });
}
