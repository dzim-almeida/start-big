/**
 * useOSFormContext.ts
 * Contexto compartilhado via provide/inject para o formulario de OS
 * Elimina a necessidade de passar props entre componentes pai e filho
 */
import { inject, provide, type InjectionKey, type Ref, type ComputedRef } from 'vue';

import type { OSFormData, OSItemForm } from './useOSFormState';
import type { OrdemServicoStatus, OrdemServicoPrioridade } from '../types/ordemServico.types';

// Tipos para as opcoes de select
export interface SelectOption {
  value: string;
  label: string;
}

export interface StatusOption {
  value: OrdemServicoStatus;
  label: string;
  color: string;
}

export interface PrioridadeOption {
  value: OrdemServicoPrioridade;
  label: string;
  color: string;
}

// Interface do contexto completo
export interface OSFormContext {
  // Estado do formulario
  form: Ref<OSFormData>;
  itens: Ref<OSItemForm[]>;
  apiError: Ref<string | null>;

  // Validacao campo-a-campo
  hasAttemptedSubmit: Ref<boolean>;
  fieldErrors: Ref<Record<string, string>>;

  // Opcoes de selects
  servicosOptions: ComputedRef<SelectOption[]>;
  produtosOptions: ComputedRef<SelectOption[]>;
  funcionariosOptions: ComputedRef<SelectOption[]>;
  statusOptions: readonly StatusOption[];
  prioridadeOptions: readonly PrioridadeOption[];

  // Estados de loading
  isLoadingServicos: Ref<boolean>;
  isLoadingProdutos: Ref<boolean>;

  // Valores financeiros
  subtotal: ComputedRef<number>;
  valorDesconto: ComputedRef<number>;
  valorTaxaEntrega: ComputedRef<number>;
  valorTotal: ComputedRef<number>;

  // Estados computados
  isEditMode: ComputedRef<boolean>;
  isFinalizada: ComputedRef<boolean>;
  isStructureLocked: ComputedRef<boolean>;
  isItemsLocked: ComputedRef<boolean>;
  isPending: ComputedRef<boolean>;

  // Acoes do formulario
  addItem: (item: OSItemForm) => { merged: boolean; newQuantity: number };
  removeItem: (index: number) => void;
  setError: (msg: string) => void;
  clearError: () => void;

  // Formatadores
  formatCurrency: (value: number) => string;
}

// Chave de injecao tipada
export const OS_FORM_CONTEXT_KEY: InjectionKey<OSFormContext> = Symbol('os-form-context');

/**
 * Provedor do contexto - usar no componente pai (OSFormModal)
 */
export function provideOSFormContext(context: OSFormContext): void {
  provide(OS_FORM_CONTEXT_KEY, context);
}

/**
 * Consumidor do contexto - usar nos componentes filhos
 * @throws Error se usado fora do provedor
 */
export function useOSFormContext(): OSFormContext {
  const context = inject(OS_FORM_CONTEXT_KEY);

  if (!context) {
    throw new Error(
      '[useOSFormContext] Deve ser usado dentro de um componente que possui provideOSFormContext'
    );
  }

  return context;
}

/**
 * Consumidor opcional - retorna undefined se fora do provedor
 * Util para componentes que podem ser usados standalone
 */
export function useOSFormContextOptional(): OSFormContext | undefined {
  return inject(OS_FORM_CONTEXT_KEY);
}
