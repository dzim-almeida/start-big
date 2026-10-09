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
/** Abriu já num tipo (ex.: "Cadastrar arquiteto" do orçamento): sem o seletor e sem "Voltar". */
const tipoFixo = ref(false);
/** Chamado com o fornecedor recém-criado (ex.: o orçamento seleciona o arquiteto novo). */
let aoCriar: ((fornecedor: FornecedorReadType) => void) | null = null;

export function useFornecedorModal() {
  function openCreateModal() {
    selectedFornecedor.value = null;
    selectedTipo.value = null;
    tipoFixo.value = false;
    aoCriar = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  /**
   * Cadastro já num tipo, avisando quem abriu quando o fornecedor nascer
   * (Spec 09B D4-D5; mesmo padrão do cadastro de cliente). O `openCreateModal`
   * de sempre não muda: continua começando pelo seletor de tipo.
   */
  function openCreateModalWithCallback(tipo: SupplierTipo, callback: (fornecedor: FornecedorReadType) => void) {
    selectedFornecedor.value = null;
    selectedTipo.value = tipo;
    tipoFixo.value = true;
    aoCriar = callback;
    mode.value = 'create';
    isOpen.value = true;
  }

  /** Entrega o fornecedor criado a quem abriu (uma vez só) e esquece o callback. */
  function avisarCriado(fornecedor: FornecedorReadType) {
    const callback = aoCriar;
    aoCriar = null;
    callback?.(fornecedor);
  }

  function openEditModal(fornecedor: FornecedorReadType) {
    tipoFixo.value = false;
    aoCriar = null;
    selectedFornecedor.value = fornecedor;
    selectedTipo.value = (fornecedor.tipo as SupplierTipo) || 'produto';
    mode.value = 'edit';
    isOpen.value = true;
  }

  function openViewModal(fornecedor: FornecedorReadType) {
    tipoFixo.value = false;
    aoCriar = null;
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
      tipoFixo.value = false;
      aoCriar = null;
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
    tipoFixo,
    isCreateMode,
    isEditMode,
    isViewMode,
    isTipoSelectionStep,
    modalTitle,
    openCreateModal,
    openCreateModalWithCallback,
    avisarCriado,
    openEditModal,
    openViewModal,
    selectTipo,
    backToTipoSelection,
    closeModal,
  };
}
