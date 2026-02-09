import { computed, ref } from 'vue';
import type { ModalMode, ServicoRead } from '../types/servicos.types';

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedServico = ref<ServicoRead | null>(null);

export function useServicoModal() {
  function openCreateModal() {
    selectedServico.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  function openEditModal(servico: ServicoRead) {
    selectedServico.value = servico;
    mode.value = 'edit';
    isOpen.value = true;
  }

  function openViewModal(servico: ServicoRead) {
    selectedServico.value = servico;
    mode.value = 'view';
    isOpen.value = true;
  }

  function closeModal() {
    isOpen.value = false;
    setTimeout(() => {
      selectedServico.value = null;
      mode.value = 'create';
    }, 300);
  }

  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    switch (mode.value) {
      case 'create':
        return 'Novo Serviço';
      case 'edit':
        return 'Editar Serviço';
      case 'view':
        return 'Detalhes do Serviço';
      default:
        return 'Serviço';
    }
  });

  return {
    isOpen,
    mode,
    selectedServico,
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
