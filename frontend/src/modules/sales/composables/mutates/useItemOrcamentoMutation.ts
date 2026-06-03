import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { orcamentoService } from '../../orcamento.service';

import {
  ProductSaleCreate,
  ProductSaleUpdate,
  ProductAlteration,
} from '../../schemas/productSale.schema';

import { orcamentoKeys } from '../../query.keys';
import { OrcamentoRead } from '../../schemas/orcamento.schema';

function patchOrcamentoDraftCache(
  queryClient: ReturnType<typeof useQueryClient>,
  orcamentoId: number,
  response: ProductAlteration,
) {
  queryClient.setQueryData<OrcamentoRead>(
    orcamentoKeys.draft(orcamentoId),
    (oldDraft) => {
      if (!oldDraft) return oldDraft;

      const productsList = [...(oldDraft.produtos || [])];

      const oldProductIndex = productsList.findIndex((p) => p.id === response.produto_adicionado.id);

      if (oldProductIndex === -1) {
        productsList.push(response.produto_adicionado);
      } else {
        productsList[oldProductIndex] = response.produto_adicionado;
      }

      return {
        ...oldDraft,
        produtos: productsList,
        descontos: response.financeiro_atualizado.descontos,
        entrega: response.financeiro_atualizado.entrega,
        subtotal: response.financeiro_atualizado.subtotal,
        total: response.financeiro_atualizado.total,
      };
    },
  );
  queryClient.invalidateQueries({
    queryKey: orcamentoKeys.lists(),
  });
}

export function useAddItemOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<ProductAlteration, AxiosError<ApiError>, { orcamentoId: number; payload: ProductSaleCreate }>({
    mutationFn: (variables) => orcamentoService.addItemInOrcamento(variables.orcamentoId, variables.payload),

    onSuccess: (response, { orcamentoId }) => {
      toast.success('Produto adicionado');
      patchOrcamentoDraftCache(queryClient, orcamentoId, response);
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao adicionar produto'));
    },
  });
}

export function useUpdateItemOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<
    ProductAlteration,
    AxiosError<ApiError>,
    { orcamentoId: number; productId: number; payload: ProductSaleUpdate }
  >({
    mutationFn: (variables) =>
      orcamentoService.updateItemInOrcamento(variables.orcamentoId, variables.productId, variables.payload),

    onSuccess: (response, { orcamentoId }) => {
      toast.success('Item atualizado');
      patchOrcamentoDraftCache(queryClient, orcamentoId, response);
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar item'));
    },
  });
}

export function useDeleteItemOrcamentoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<OrcamentoRead, AxiosError<ApiError>, { orcamentoId: number; productId: number }>({
    mutationFn: (variables) => orcamentoService.deleteItemInOrcamento(variables.orcamentoId, variables.productId),

    onSuccess: (updatedOrcamento, { orcamentoId }) => {
      toast.success('Item removido');
      queryClient.setQueryData(orcamentoKeys.draft(orcamentoId), updatedOrcamento);
      queryClient.invalidateQueries({
        queryKey: orcamentoKeys.lists(),
      });
    },

    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao remover item'));
    },
  });
}
