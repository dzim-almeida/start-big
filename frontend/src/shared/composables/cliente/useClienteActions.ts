/**
 * ===========================================================================
 * ARQUIVO: useClienteActions.ts
 * MODULO: Shared/Cliente
 * DESCRICAO: Composable centralizado para acoes de escrita (Mutations) de Clientes.
 * ===========================================================================
 */

import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import type { ApiError } from '@/shared/types/axios.types';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import {
  createClientePF,
  createClientePJ,
  updateCliente,
  toggleClienteAtivo
} from '@/modules/customers/services/cliente.service';
import type {
  ClientePFCreate,
  ClientePJCreate,
  ClientePFUpdate,
  ClientePJUpdate,
  ClienteRead
} from '@/modules/customers/types/clientes.types';

import { unmaskDocument, unmaskPhone } from '@/shared/utils/unmask.utils';

export function useClienteActions() {
  const toast = useToast();
  const queryClient = useQueryClient();

  // ===========================================================================
  // CREATE PF
  // ===========================================================================
  const createPFMutation = useMutation<ClienteRead, AxiosError<ApiError>, ClientePFCreate>({
    mutationFn: (data) => {
      const payload = {
        ...data,
        cpf: data.cpf ? unmaskDocument(data.cpf) : '',
        celular: data.celular ? unmaskPhone(data.celular) : undefined,
      };
      return createClientePF(payload);
    },
    onSuccess: () => {
      toast.success('Cliente PF cadastrado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['clientes'] });
    },
    onError: (error) => {
      console.error('[useClienteActions] Error create PF:', error);
      toast.error(getErrorMessage(error, 'Erro ao criar cliente PF') as string);
    }
  });

  // ===========================================================================
  // CREATE PJ
  // ===========================================================================
  const createPJMutation = useMutation<ClienteRead, AxiosError<ApiError>, ClientePJCreate>({
    mutationFn: (data) => {
      const payload = {
        ...data,
        cnpj: data.cnpj ? unmaskDocument(data.cnpj) : '',
        celular: data.celular ? unmaskPhone(data.celular) : undefined,
      };
      return createClientePJ(payload);
    },
    onSuccess: () => {
      toast.success('Cliente PJ cadastrado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['clientes'] });
    },
    onError: (error) => {
      console.error('[useClienteActions] Error create PJ:', error);
      toast.error(getErrorMessage(error, 'Erro ao criar cliente PJ') as string);
    }
  });

  // ===========================================================================
  // UPDATE
  // ===========================================================================
  const updateMutation = useMutation<
    ClienteRead,
    AxiosError<ApiError>,
    { id: number; data: ClientePFUpdate | ClientePJUpdate }
  >({
    mutationFn: ({ id, data }) => updateCliente(id, data),
    onSuccess: () => {
      toast.success('Cliente atualizado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['clientes'] });
    },
    onError: (error) => {
        console.error('[useClienteActions] Error update:', error);
        toast.error(getErrorMessage(error, 'Erro ao atualizar cliente') as string);
    }
  });

  // ===========================================================================
  // TOGGLE STATUS
  // ===========================================================================
  const toggleAtivoMutation = useMutation<ClienteRead, AxiosError<ApiError>, number>({
    mutationFn: toggleClienteAtivo,
    onSuccess: (data) => {
      const status = data.ativo ? 'ativado' : 'desativado';
      toast.success(`Cliente ${status} com sucesso!`);

      // Atualiza o cache manualmente para feedback imediato na UI
      queryClient.setQueryData<ClienteRead[]>(['clientes'], (oldData) => {
        if (!oldData) return [];
        return oldData.map((cliente) => 
          cliente.id === data.id ? data : cliente
        );
      });

      // Garante que o servidor seja a fonte da verdade em seguida
      queryClient.invalidateQueries({ queryKey: ['clientes'] });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Erro ao alterar status do cliente') as string);
    },
  });

  return {
    createPFMutation,
    createPJMutation,
    updateMutation,
    toggleAtivoMutation,
    // Helpers para facilitar o uso no template se necessario
    isPending: (
        createPFMutation.isPending.value || 
        createPJMutation.isPending.value || 
        updateMutation.isPending.value ||
        toggleAtivoMutation.isPending.value
    )
  };
}
