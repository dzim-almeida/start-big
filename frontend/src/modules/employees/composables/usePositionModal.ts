/**
 * @fileoverview Modal state management for cargos
 */

import { ref, computed } from 'vue';
import type { CargoRead } from '../types/positions.types';

const isOpen = ref(false);
const mode = ref<'create' | 'edit' | 'view'>('create');
const selectedPosition = ref<CargoRead | null>(null);

export function usePositionModal() {
  function openCreateModal() {
    selectedPosition.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  function openEditModal(position: CargoRead) {
    selectedPosition.value = position;
    mode.value = 'edit';
    isOpen.value = true;
  }

  function openViewModal(position: CargoRead) {
    selectedPosition.value = position;
    mode.value = 'view';
    isOpen.value = true;
  }

  function closeModal() {
    isOpen.value = false;
    setTimeout(() => {
      selectedPosition.value = null;
      mode.value = 'create';
    }, 300);
  }

  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    switch (mode.value) {
      case 'create':
        return 'Novo Cargo';
      case 'edit':
        return 'Editar Cargo';
      case 'view':
        return 'Detalhes do Cargo';
      default:
        return 'Cargo';
    }
  });

  return {
    isOpen,
    mode,
    selectedPosition,
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
