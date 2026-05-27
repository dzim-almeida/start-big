/**
 * @fileoverview Modal state management composable
 * @description Manages modal open/close state and mode (create/edit/view)
 */

import { ref, computed } from 'vue';
import type { ModalMode, ProdutoRead } from '../types/products.types';

// =============================================
// Shared State (singleton pattern)
// =============================================

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedProduct = ref<ProdutoRead | null>(null);

// =============================================
// Composable
// =============================================

export function useProductModal() {
  /**
   * Opens modal in create mode
   */
  function openCreateModal() {
    selectedProduct.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  /**
   * Opens modal in edit mode with product data
   * @param product - Product to edit
   */
  function openEditModal(product: ProdutoRead) {
    selectedProduct.value = product;
    mode.value = 'edit';
    isOpen.value = true;
  }

  /**
   * Opens modal in view mode (read-only)
   * @param product - Product to view
   */
  function openViewModal(product: ProdutoRead) {
    selectedProduct.value = product;
    mode.value = 'view';
    isOpen.value = true;
  }

  /**
   * Closes modal and resets state after animation
   */
  function closeModal() {
    isOpen.value = false;
    setTimeout(() => {
      selectedProduct.value = null;
      mode.value = 'create';
    }, 300);
  }

  // Computed helpers
  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    switch (mode.value) {
      case 'create':
        return 'Novo Produto';
      case 'edit':
        return 'Editar Produto';
      case 'view':
        return 'Detalhes do Produto';
      default:
        return 'Produto';
    }
  });

  return {
    isOpen,
    mode,
    selectedProduct,
    isCreateMode,
    isEditMode,
    isViewMode,
    modalTitle,
    openCreateModal,
    openEditModal,
    openViewModal,
    closeModal,
  };
}
