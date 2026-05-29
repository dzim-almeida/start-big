/**
 * @fileoverview Modal state management composable
 * @description Manages modal open/close state and mode (create/edit/view)
 */

import { ref, computed } from 'vue';
import type { ModalMode, FuncionarioRead } from '../types/employees.types';

// =============================================
// Shared State (singleton pattern)
// =============================================

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedEmployee = ref<FuncionarioRead | null>(null);

// =============================================
// Composable
// =============================================

export function useEmployeeModal() {
  /**
   * Opens modal in create mode
   */
  function openCreateModal() {
    selectedEmployee.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  /**
   * Opens modal in edit mode with employee data
   * @param employee - Employee to edit
   */
  function openEditModal(employee: FuncionarioRead) {
    selectedEmployee.value = employee;
    mode.value = 'edit';
    isOpen.value = true;
  }

  /**
   * Opens modal in view mode (read-only)
   * @param employee - Employee to view
   */
  function openViewModal(employee: FuncionarioRead) {
    selectedEmployee.value = employee;
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
      selectedEmployee.value = null;
    }, 300);
  }

  // Computed helpers
  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    switch (mode.value) {
      case 'create':
        return 'Novo Funcionario';
      case 'edit':
        return 'Editar Funcionario';
      case 'view':
        return 'Detalhes do Funcionario';
      default:
        return 'Funcionario';
    }
  });

  return {
    // State
    isOpen,
    mode,
    selectedEmployee,

    // Computed
    isCreateMode,
    isEditMode,
    isViewMode,
    modalTitle,

    // Actions
    openCreateModal,
    openEditModal,
    openViewModal,
    closeModal,
  };
}
