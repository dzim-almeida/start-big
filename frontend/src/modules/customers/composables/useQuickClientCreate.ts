/**
 * ===========================================================================
 * ARQUIVO: useQuickClientCreate.ts
 * MODULO: Clientes
 * DESCRICAO: Composable para criacao rapida de clientes (PF/PJ) em modais
 *            de busca. Utiliza as acoes globais do useClienteActions.
 * ===========================================================================
 */

import { ref } from 'vue';
import { useClienteActions } from '@/shared/composables/cliente/useClienteActions';
import type { TipoCliente, Cliente } from '../types/clientes.types';

// ===========================================================================
// INTERFACES
// ===========================================================================

interface QuickClientePF {
  nome: string;
  cpf: string;
  celular: string;
}

interface QuickClientePJ {
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  celular: string;
  responsavel: string;
}

// ===========================================================================
// COMPOSABLE
// ===========================================================================

export function useQuickClientCreate() {
  const { createPFMutation, createPJMutation } = useClienteActions();

  // ===========================================================================
  // STATE
  // ===========================================================================

  const isCreating = ref(false);
  const creatingType = ref<TipoCliente>('PF');
  const isSubmitting = ref(false);

  const newClientePf = ref<QuickClientePF>({
    nome: '',
    cpf: '',
    celular: '',
  });

  const newClientePj = ref<QuickClientePJ>({
    razao_social: '',
    nome_fantasia: '',
    cnpj: '',
    celular: '',
    responsavel: '',
  });

  // ===========================================================================
  // ACTIONS
  // ===========================================================================

  function toggleCreateMode(tipo?: TipoCliente) {
    if (tipo) {
      creatingType.value = tipo;
      isCreating.value = true;
    } else {
      isCreating.value = !isCreating.value;
    }
  }

  function resetCreateForm() {
    isCreating.value = false;
    creatingType.value = 'PF';
    newClientePf.value = { nome: '', cpf: '', celular: '' };
    newClientePj.value = { razao_social: '', nome_fantasia: '', cnpj: '', celular: '', responsavel: '' };
  }

  async function submitQuickCreate(): Promise<Cliente | null> {
    isSubmitting.value = true;

    try {
      if (creatingType.value === 'PF') {
        const payload = {
          tipo: 'PF' as const,
          nome: newClientePf.value.nome,
          cpf: newClientePf.value.cpf || undefined,
          celular: newClientePf.value.celular || undefined,
        };
        const result = await createPFMutation.mutateAsync(payload);
        resetCreateForm();
        return result as Cliente;
      } else {
        const payload = {
          tipo: 'PJ' as const,
          razao_social: newClientePj.value.razao_social,
          nome_fantasia: newClientePj.value.nome_fantasia || undefined,
          cnpj: newClientePj.value.cnpj || undefined,
          celular: newClientePj.value.celular || undefined,
          responsavel: newClientePj.value.responsavel || undefined,
        };
        const result = await createPJMutation.mutateAsync(payload);
        resetCreateForm();
        return result as Cliente;
      }
    } catch (error) {
      // Erro já é tratado pelo useClienteActions (toast)
      return null;
    } finally {
      isSubmitting.value = false;
    }
  }

  // ===========================================================================
  // RETURN
  // ===========================================================================

  return {
    // State
    isCreating,
    creatingType,
    isSubmitting,
    newClientePf,
    newClientePj,

    // Actions
    toggleCreateMode,
    resetCreateForm,
    submitQuickCreate,
  };
}
