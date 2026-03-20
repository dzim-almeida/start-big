import { computed, ref } from 'vue';
import type { ModalMode } from '../types/fornecedor.types';
import type { FornecedorReadType } from '../schemas/fornecedor.schema';

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedFornecedor = ref<FornecedorReadType | null>(null);

export function useFornecedorModal() {
  function openCreateModal() {
    selectedFornecedor.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  function openEditModal(fornecedor: FornecedorReadType) {
    selectedFornecedor.value = fornecedor;
    mode.value = 'edit';
    isOpen.value = true;
  }

  function openViewModal(fornecedor: FornecedorReadType) {
    selectedFornecedor.value = fornecedor;
    mode.value = 'view';
    isOpen.value = true;
  }

  function closeModal() {
    isOpen.value = false;
    setTimeout(() => {
      selectedFornecedor.value = null;
      mode.value = 'create';
    }, 300);
  }

  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    switch (mode.value) {
      case 'create':
        return 'Novo Fornecedor';
      case 'edit':
        return 'Editar Fornecedor';
      case 'view':
        return 'Detalhes do Fornecedor';
      default:
        return 'Fornecedor';
    }
  });

  return {
    isOpen,
    mode,
    selectedFornecedor,
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
