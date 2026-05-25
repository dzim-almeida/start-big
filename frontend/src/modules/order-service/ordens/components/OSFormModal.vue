<script setup lang="ts">
import { ref, computed } from 'vue';
import OSFormModalShell from './form/OSFormModalShell.vue';
import OSFormAuxModals from './form/OSFormAuxModals.vue';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../schemas/relationship/customer/customer.schema';
import { getUniqueOS } from '../services/orderServiceGet.service';
import { uploadFotoOS } from '../services/relationship/osPhotoMutate.service';
import { useOSFormProvider, useOSFormPendingState } from '../context/useForm.context';
import { useCreateItemOSMutation } from '../composables/request/useOrderServiceCreate.mutate';
import { useReopenOrderServiceMutation } from '../composables/request/useOrderServiceUpdate.mutate';
import { useOrderServiceDeleteItem } from '../composables/request/useOrderServiceDelete.mutate';
import { useOSStatusLocks } from '../composables/modal/useOSStatusLocks';
import { useOSFinancialSummary } from '../composables/modal/useOSFinancialSummary';
import { useOSFormAdapter } from '../composables/modal/useOSFormAdapter';
import { useOSPendingPhotos } from '../composables/modal/useOSPendingPhotos';
import { useOSEquipmentHistory } from '../composables/modal/useOSEquipmentHistory';
import { useOSReopenState } from '../composables/modal/useOSReopenState';
import { useOSItemsManager } from '../composables/modal/useOSItemsManager';
import { useOSModalLifecycle } from '../composables/modal/useOSModalLifecycle';
import { useOSSelectOptions } from '../composables/modal/useOSSelectOptions';
import { useOSPrintFlow } from '../composables/modal/useOSPrintFlow';
import { useOSClientHistory } from '../composables/modal/useOSClientHistory';
import { useOSFormViewProvider } from '../context/useOSFormView.context';
interface Props {
  isOpen: boolean;
  ordemServico?: OrderServiceReadDataType | null;
  selectedCliente?: CustomerUnionReadSchemaDataType | null;
}
const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
  changeCliente: [];
}>();
let closeItemModalProxy: (() => void) | null = null;
function closeItemModal() {
  closeItemModalProxy?.();
}
const localOSData = ref<OrderServiceReadDataType | null>(null);
const currentOSData = computed(() => localOSData.value ?? props.ordemServico ?? null);
const osNumber = computed(() => currentOSData.value?.numero_os ?? null);
const isCreateMode = computed(() => !props.ordemServico);

const {
  printType,
  printFormat,
  isFinalizarModalOpen,
  isPrintSelectModalOpen,
  printEntrada,
  printSaida,
  printEntradaAndClose,
  handleFinalizarOS,
  closeFinalizarModal,
  onFinalized,
  handlePrintFormatSelected,
  closePrintSelectModal,
} = useOSPrintFlow({
  onClose: handleClose,
});

const form = useOSFormProvider({
  osNumber,
  isCreateMode,
  onCreateSuccess: (os: OrderServiceReadDataType) => {
    localOSData.value = os;
    printEntradaAndClose();
  },
  onUpdateSuccess: async () => {
    await uploadPendingPhotos();
    handleClose();
  },
  onItemSuccess: () => closeItemModal(),
  onFinalizarSuccess: () => { isFinalizarModalOpen.value = false; },
});

const isPending = useOSFormPendingState(form);
const isEditMode = computed(() => !isCreateMode.value);
const isFinalizada = computed(() => currentOSData.value?.status === 'FINALIZADA');
const isCancelada = computed(() => currentOSData.value?.status === 'CANCELADA');
const { funcionariosOptions, statusOptions, prioridadeOptions } = useOSSelectOptions({
  currentStatus: computed(() => currentOSData.value?.status),
});
const reopenMutation = useReopenOrderServiceMutation();
const {
  isReopenOptionsOpen,
  reopenMode,
  handleReopenClick,
  handleReopenCancel,
  handleReopenTextOnly,
  handleReopenFull,
  resetReopenState,
} = useOSReopenState({
  osNumber,
  onReopenRequest: (numeroOS) => reopenMutation.mutate(numeroOS),
  onFullReopen: () => handleClose(),
});
const { isStructureLocked, isItemsLocked } = useOSStatusLocks({ isFinalizada, isCancelada, reopenMode });
const addItemMutation = useCreateItemOSMutation();
const deleteItemMutation = useOrderServiceDeleteItem();

async function refreshCurrentOSData() {
  if (!osNumber.value) return;
  const os = await getUniqueOS(osNumber.value);
  localOSData.value = os;
}
const {
  isItemModalOpen,
  editingItem,
  displayItems,
  openAddItemModal,
  openEditItemModal,
  closeItemModal: closeItemModalFromManager,
  handleSaveItem,
  handleRemoveItem,
} = useOSItemsManager({
  isCreateMode,
  osNumber,
  createItems: computed(() => form.criar.itens.value.map(entry => entry.value)),
  currentOSData,
  form,
  addItemMutation,
  deleteItemMutation,
  refreshCurrentOSData,
  setCurrentOSData: (os) => {
    localOSData.value = os;
  },
});
closeItemModalProxy = closeItemModalFromManager;
const {
  displaySubtotal,
  displayValorEntrega,
  displayValorDesconto,
  displayValorTotal,
  displayValorEntrada,
  handleValorEntradaUpdate,
} = useOSFinancialSummary({
  isCreateMode,
  createItems: computed(() => form.criar.itens.value.map(item => item.value)),
  currentOSData,
  createDesconto: form.criar.desconto,
  createValorEntrada: form.criar.valor_entrada,
  updateValorEntrada: form.atualizarGeral.valor_entrada,
});
const {
  pendingPhotos,
  handleAddPhoto,
  handleRemovePending,
  clearPendingPhotos,
  uploadPendingPhotos,
} = useOSPendingPhotos({
  osNumber,
  uploadPhoto: uploadFotoOS,
});

function handlePhotoChange() {
  refreshCurrentOSData();
}
function handleLocalSubmit() {
  if (isCreateMode.value) {
    const clienteId = (props.selectedCliente as { id?: number } | null)?.id;
    if (clienteId) form.criar.cliente_id.value = clienteId;
    form.criar.onSubmit();
  } else if (reopenMode.value === 'TEXT_ONLY') {
    form.atualizarGeral.status.value = 'FINALIZADA';
    form.atualizarGeral.onSubmit();
  } else {
    form.atualizarGeral.onSubmit();
  }
}
function handleClose() {
  form.criar.resetForm();
  form.atualizarGeral.resetForm();
  form.atualizarEquipamento.resetForm();
  form.item.resetForm();
  clearPendingPhotos();
  resetReopenState();
  localOSData.value = null;
  updatedClienteRef.value = null;
  emit('close');
}

useOSModalLifecycle({
  isOpen: computed(() => props.isOpen),
  ordemServico: computed(() => props.ordemServico),
  selectedCliente: computed(() => props.selectedCliente),
  currentOSData,
  localOSData,
  isCreateMode,
  reopenMode,
  form,
  resetReopenState,
  onOpen: () => {
    // reservado para estados locais na abertura do modal
  },
});
const {
  equipamentosHistorico,
  selectedHistorico,
  isEquipSelectModalOpen,
  handleEquipamentoSelected,
  applyEquipamentoHistorico,
} = useOSEquipmentHistory({
  selectedCliente: computed(() => props.selectedCliente as { id?: number } | null),
  ordemServicoCliente: computed(() => currentOSData.value?.cliente as { id?: number } | null),
  isCreateMode,
  createEquipamentoTipo: form.criar.equipamento_tipo_equipamento,
  createEquipamentoMarca: form.criar.equipamento_marca,
  createEquipamentoModelo: form.criar.equipamento_modelo,
  createEquipamentoNumeroSerie: form.criar.equipamento_numero_serie,
});
const {
  equipamentoFormData,
  controlsStatus,
  controlsFuncionarioId,
  controlsPrioridade,
  controlsDataPrevisao,
  handleStatusUpdate,
  handleFuncionarioIdUpdate,
  handlePrioridadeUpdate,
  handleDataPrevisaoUpdate,
  currentDiagnostico,
  handleDiagnosticoUpdate,
} = useOSFormAdapter({
  form,
  isCreateMode,
});
const updatedClienteRef = ref<CustomerUnionReadSchemaDataType | null>(null);
const currentCliente = computed(
  () => updatedClienteRef.value ?? props.selectedCliente ?? currentOSData.value?.cliente ?? null,
);

function handleUpdateCliente(cliente: CustomerUnionReadSchemaDataType) {
  updatedClienteRef.value = cliente;
}

function handleChangeCliente() {
  emit('changeCliente');
}

function setEquipamentoFormData(value: typeof equipamentoFormData.value) {
  equipamentoFormData.value = value;
}

const {
  isHistoricoModalOpen,
  openHistoricoModal,
  closeHistoricoModal,
  reutilizarEquipamento,
} = useOSClientHistory({ setEquipamentoFormData });

function setSelectedHistorico(value: string) {
  selectedHistorico.value = value;
}

function closeEquipamentoModal() {
  isEquipSelectModalOpen.value = false;
}

useOSFormViewProvider({
  isOpen: computed(() => props.isOpen),
  currentOSData,
  currentCliente,
  osNumber,
  isCreateMode,
  isEditMode,
  isPending,
  isFinalizada,
  isCancelada,
  reopenMode,
  isStructureLocked,
  isItemsLocked,
  controlsStatus,
  controlsFuncionarioId,
  controlsPrioridade,
  controlsDataPrevisao,
  statusOptions,
  prioridadeOptions,
  funcionariosOptions,
  displayItems,
  displaySubtotal,
  displayValorEntrega,
  displayValorDesconto,
  displayValorTotal,
  displayValorEntrada,
  equipamentoFormData,
  equipamentosHistorico,
  selectedHistorico,
  currentDiagnostico,
  pendingPhotos,
  isReopenOptionsOpen,
  printType,
  printFormat,
  isPrintSelectModalOpen,
  isFinalizarModalOpen,
  isItemModalOpen,
  editingItem,
  isEquipSelectModalOpen,
  handleClose,
  handleLocalSubmit,
  handleFinalizarOS,
  printEntrada,
  printSaida,
  handleReopenClick,
  handleChangeCliente,
  handleUpdateCliente,
  handleStatusUpdate,
  handleFuncionarioIdUpdate,
  handlePrioridadeUpdate,
  handleDataPrevisaoUpdate,
  handleValorEntradaUpdate,
  setEquipamentoFormData,
  setSelectedHistorico,
  applyEquipamentoHistorico,
  handleDiagnosticoUpdate,
  handleAddPhoto,
  handleRemovePending,
  handlePhotoChange,
  openAddItemModal,
  openEditItemModal,
  handleRemoveItem,
  handleReopenCancel,
  handleReopenTextOnly,
  handleReopenFull,
  closeFinalizarModal,
  onFinalized,
  handlePrintFormatSelected,
  closePrintSelectModal,
  closeItemModal,
  handleSaveItem,
  closeEquipamentoModal,
  handleEquipamentoSelected,
  isHistoricoModalOpen,
  openHistoricoModal,
  closeHistoricoModal,
  reutilizarEquipamento,
});
</script>

<template>
  <OSFormModalShell />
  <OSFormAuxModals />
</template>
