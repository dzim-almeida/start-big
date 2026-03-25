// ============================================================================
// MÓDULO: FornecedorModalState (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Controlar a abertura, fechamento e fluxo interno do modal.
// FUNCIONALIDADES: Gestão de modos (Create/Edit/View), navegação entre etapas 
//                  de seleção de tipo e limpeza de estado pós-fechamento.
// ============================================================================
import { computed, ref } from 'vue';
import type { ModalMode, SupplierTipo } from '../types/fornecedor.types';
import type { FornecedorReadType } from '../schemas/fornecedor.schema';

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedFornecedor = ref<FornecedorReadType | null>(null);
const selectedTipo = ref<SupplierTipo | null>(null);

export function useFornecedorModal() {
  function openCreateModal() {
    selectedFornecedor.value = null;
    selectedTipo.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  function openEditModal(fornecedor: FornecedorReadType) {
    selectedFornecedor.value = fornecedor;
    selectedTipo.value = (fornecedor.tipo as SupplierTipo) || 'produto';
    mode.value = 'edit';
    isOpen.value = true;
  }

  function openViewModal(fornecedor: FornecedorReadType) {
    selectedFornecedor.value = fornecedor;
    selectedTipo.value = (fornecedor.tipo as SupplierTipo) || 'produto';
    mode.value = 'view';
    isOpen.value = true;
  }

  function selectTipo(tipo: SupplierTipo) {
    selectedTipo.value = tipo;
  }

  function backToTipoSelection() {
    selectedTipo.value = null;
  }

  function closeModal() {
    isOpen.value = false;
    setTimeout(() => {
      selectedFornecedor.value = null;
      selectedTipo.value = null;
      mode.value = 'create';
    }, 300);
  }

  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const isTipoSelectionStep = computed(
    () => mode.value === 'create' && selectedTipo.value === null,
  );

  const modalTitle = computed(() => {
    if (isTipoSelectionStep.value) return 'Novo Fornecedor';
    switch (mode.value) {
      case 'create':
        return 'Cadastrar Fornecedor';
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
    selectedTipo,
    isCreateMode,
    isEditMode,
    isViewMode,
    isTipoSelectionStep,
    modalTitle,
    openCreateModal,
    openEditModal,
    openViewModal,
    selectTipo,
    backToTipoSelection,
    closeModal,
  };
}
