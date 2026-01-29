/**
 * @fileoverview Modal state management composable for customers
 * @description Manages modal open/close state and mode (create/edit/view)
 * Uses singleton pattern with module-level refs for shared state
 */

import { ref, computed } from 'vue';
import type { Cliente } from '../types/clientes.types';

// =============================================
// Types
// =============================================

export type ModalMode = 'create' | 'edit' | 'view';

// =============================================
// Shared State (singleton pattern)
// =============================================

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedCustomer = ref<Cliente | null>(null);

// =============================================
// Composable
// =============================================

export function useCustomerModal() {
  /**
   * Opens modal in create mode
   */
  function openCreateModal() {
    selectedCustomer.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  /**
   * Opens modal in edit mode with customer data
   * @param customer - Customer to edit
   */
  function openEditModal(customer: Cliente) {
    selectedCustomer.value = customer;
    mode.value = 'edit';
    isOpen.value = true;
  }

  /**
   * Opens modal in view mode (read-only)
   * @param customer - Customer to view
   */
  function openViewModal(customer: Cliente) {
    selectedCustomer.value = customer;
    mode.value = 'view';
    isOpen.value = true;
  }

  /**
   * Closes modal and resets state after animation
   */
  function closeModal() {
    isOpen.value = false;
    // Delay reset to allow animation to complete
    setTimeout(() => {
      selectedCustomer.value = null;
      mode.value = 'create';
    }, 300);
  }

  // Computed helpers
  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    if (!isCreateMode.value && selectedCustomer.value) {
      const customerType = selectedCustomer.value.tipo;
      if (mode.value === 'edit') {
        return customerType === 'PF' ? 'Editar Cliente PF' : 'Editar Cliente PJ';
      }
      return customerType === 'PF' ? 'Detalhes do Cliente PF' : 'Detalhes do Cliente PJ';
    }
    return 'Novo Cliente';
  });

  const modalSubtitle = computed(() => {
    if (selectedCustomer.value) {
      if (selectedCustomer.value.tipo === 'PF') {
        return selectedCustomer.value.nome;
      }
      return selectedCustomer.value.nome_fantasia || selectedCustomer.value.razao_social;
    }
    return 'Preencha os dados do cliente';
  });

  return {
    // State
    isOpen,
    mode,
    selectedCustomer,

    // Computed
    isCreateMode,
    isEditMode,
    isViewMode,
    modalTitle,
    modalSubtitle,

    // Actions
    openCreateModal,
    openEditModal,
    openViewModal,
    closeModal,
  };
}
