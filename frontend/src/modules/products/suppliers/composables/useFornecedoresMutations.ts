// ============================================================================
// MÓDULO: FornecedorMutations (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Gerenciar as operações de escrita (POST, PUT, PATCH) na API.
// TECNOLOGIAS: Vue Query (TanStack), Axios, Composable-based Logic.
// FUNCIONALIDADES: Criação, atualização, inversão de status (ativo/inativo) 
//                  e invalidação automática de cache para manter a UI sincronizada.
// ============================================================================
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import {
  createFornecedor,
  updateFornecedor,
  toggleFornecedorAtivo,
  type FornecedorCreatePayload,
  type FornecedorUpdatePayload,
} from '../services/fornecedor.service';
import { FORNECEDORES_QUERY_KEY } from '../../shared/constants/queryKeys';
import type { FornecedorReadType } from '../schemas/fornecedor.schema';

export function useCreateFornecedorMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<FornecedorReadType, AxiosError<ApiError>, FornecedorCreatePayload>({
    mutationFn: createFornecedor,
    onSuccess: () => {
      toast.success('Fornecedor cadastrado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [FORNECEDORES_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao cadastrar fornecedor') as string);
    },
  });
}

export function useUpdateFornecedorMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<
    FornecedorReadType,
    AxiosError<ApiError>,
    { id: number; data: FornecedorUpdatePayload }
  >({
    mutationFn: ({ id, data }) => updateFornecedor(id, data),
    onSuccess: () => {
      toast.success('Fornecedor atualizado com sucesso!');
      queryClient.invalidateQueries({ queryKey: [FORNECEDORES_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao atualizar fornecedor') as string);
    },
  });
}

export function useToggleFornecedorAtivoMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<FornecedorReadType, AxiosError<ApiError>, number>({
    mutationFn: toggleFornecedorAtivo,
    onSuccess: (data) => {
      const status = data.ativo ? 'ativado' : 'desativado';
      toast.success(`Fornecedor ${status} com sucesso!`);
      queryClient.refetchQueries({ queryKey: [FORNECEDORES_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao alterar status do fornecedor') as string);
    },
  });
}
