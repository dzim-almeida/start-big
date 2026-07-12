<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import OSFormModalShell from './form/OSFormModalShell.vue';
import OSFormAuxModals from './form/OSFormAuxModals.vue';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../schemas/relationship/customer/customer.schema';
import type { ObjetoHistorico } from '@/modules/customers/types/clientes.types';
import { getUniqueOS } from '../services/orderServiceGet.service';
import { uploadFotoOS } from '../services/relationship/osPhotoMutate.service';
import { useOSFormProvider, useOSFormPendingState } from '../context/useForm.context';
import { useCreateItemOSMutation } from '../composables/request/useOrderServiceCreate.mutate';
import { useReopenOrderServiceMutation } from '../composables/request/useOrderServiceUpdate.mutate';
import { useGerenteAprovacao } from '@/shared/composables/useGerenteAprovacao';
import { useToast } from '@/shared/composables/useToast';
import GerenteAprovacaoModal from '@/shared/components/commons/GerenteAprovacaoModal/GerenteAprovacaoModal.vue';
import { useOrderServiceDeleteItem } from '../composables/request/useOrderServiceDelete.mutate';
import { useOSStatusLocks } from '../composables/modal/useOSStatusLocks';
import { useOSFinancialSummary } from '../composables/modal/useOSFinancialSummary';
import { useOSFormAdapter } from '../composables/modal/useOSFormAdapter';
import { useOSPendingPhotos } from '../composables/modal/useOSPendingPhotos';
import { useOSObjetoHistory } from '../composables/modal/useOSObjetoHistory';
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
  initialObjeto?: ObjetoHistorico | null;
  autoUsarCredito?: boolean;
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
let resetObjetoSelectStateProxy: (() => void) | null = null;
const localOSData = ref<OrderServiceReadDataType | null>(null);
const currentOSData = computed(() => localOSData.value ?? props.ordemServico ?? null);
const osNumber = computed(() => currentOSData.value?.numero_os ?? null);
const isCreateMode = computed(() => !props.ordemServico);

// Crédito capturado ao reabrir — limita o crédito anterior ao valor que foi cobrado
// (não ao dinheiro entregue, que pode incluir troco)
const creditoAoReabrir = ref<number | null>(null);

function capturarCreditoAnterior() {
  const os = currentOSData.value;
  if (!os || !os.pagamentos?.length) { creditoAoReabrir.value = null; return; }
  const totalPago = os.pagamentos.reduce((s, p) => s + p.valor, 0);
  creditoAoReabrir.value = Math.min(totalPago, os.valor_total);
}

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
  getOS: () => currentOSData.value,
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
const gerenteReopen = useGerenteAprovacao();
const toast = useToast();

async function executarReopenOS(numeroOS: string, codigoGerente?: string): Promise<void> {
  try {
    await reopenMutation.mutateAsync({ osNumber: numeroOS, codigoGerente });
    await refreshCurrentOSData();
    capturarCreditoAnterior();
  } catch (error: any) {
    const detail = error?.response?.data?.detail;
    if (detail === 'REQUER_APROVACAO_GERENTE') {
      const pin = await gerenteReopen.pedirPin();
      if (pin) await executarReopenOS(numeroOS, pin);
    } else if (detail === 'PIN_GERENTE_INVALIDO') {
      toast.error('PIN do gerente inválido');
      const pin = await gerenteReopen.pedirPin();
      if (pin) await executarReopenOS(numeroOS, pin);
    }
  }
}

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
  onReopenRequest: (numeroOS) => void executarReopenOS(numeroOS),
  onFullReopen: () => {},
});
const { isStructureLocked, isDiagnosticoLocked, isItemsLocked } = useOSStatusLocks({ isFinalizada, isCancelada, reopenMode });
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
  displayValorAcrescimo,
  handleValorEntradaUpdate,
  handleValorEntregaUpdate,
} = useOSFinancialSummary({
  isCreateMode,
  createItems: computed(() => form.criar.itens.value.map(item => item.value)),
  currentOSData,
  createDesconto: form.criar.desconto,
  createValorEntrada: form.criar.valor_entrada,
  updateValorEntrada: form.atualizarGeral.valor_entrada,
  updateTaxaEntrega: form.atualizarGeral.taxa_entrega,
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
    form.atualizarGeral.onSubmitTextOnly();
  } else {
    form.atualizarGeral.onSubmit();
  }
}
function handleClose() {
  form.criar.resetForm();
  form.atualizarGeral.resetForm();
  form.atualizarObjeto.resetForm();
  form.item.resetForm();
  clearPendingPhotos();
  resetReopenState();
  localOSData.value = null;
  updatedClienteRef.value = null;
  creditoAoReabrir.value = null;
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
    resetObjetoSelectStateProxy?.();
    // Captura crédito se a OS já foi reaberta anteriormente (vem da tabela)
    const os = currentOSData.value;
    if (os && os.pagamentos?.length > 0 && os.status !== 'FINALIZADA' && os.status !== 'CANCELADA') {
      capturarCreditoAnterior();
    }
    if (props.initialObjeto && isCreateMode.value) {
      const objeto = props.initialObjeto;
      nextTick(() => {
        form.criar.objeto_tipo_equipamento.value = objeto.objeto;
        form.criar.objeto_marca.value = objeto.marca ?? '';
        form.criar.objeto_modelo.value = objeto.modelo ?? '';
        form.criar.objeto_numero_serie.value = objeto.numero_serie ?? '';
        form.criar.objeto_cor.value = objeto.cor ?? '';
        form.criar.objeto_dados_adicionais.value = { ...(objeto.dados_adicionais ?? {}) };
      });
    }
    if (props.autoUsarCredito && isCreateMode.value) {
      nextTick(() => handleUsarCredito());
    }
  },
});
const {
  objetosHistorico,
  selectedHistorico,
  isObjetoSelectModalOpen,
  handleObjetoSelected,
  applyObjetoHistorico,
  resetObjetoSelectState,
} = useOSObjetoHistory({
  selectedCliente: computed(() => props.selectedCliente as { id?: number } | null),
  ordemServicoCliente: computed(() => currentOSData.value?.cliente as { id?: number } | null),
  isCreateMode,
  isFormOpen: computed(() => props.isOpen),
  createObjetoTipo: form.criar.objeto_tipo_equipamento,
  createObjetoMarca: form.criar.objeto_marca,
  createObjetoModelo: form.criar.objeto_modelo,
  createObjetoNumeroSerie: form.criar.objeto_numero_serie,
  createObjetoCor: form.criar.objeto_cor,
  createObjetoDadosAdicionais: form.criar.objeto_dados_adicionais,
});
resetObjetoSelectStateProxy = resetObjetoSelectState;
const {
  objetoFormData,
  objetoDados,
  osDados,
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

const saldoCreditoCliente = computed(() => {
  const c = currentCliente.value as { saldo_credito?: number } | null;
  return c?.saldo_credito ?? 0;
});

function handleUsarCredito() {
  if (!isCreateMode.value || saldoCreditoCliente.value <= 0) return;
  form.criar.valor_entrada.value = saldoCreditoCliente.value;
  form.criar.usar_credito_cliente.value = true;
}

function handleUpdateCliente(cliente: CustomerUnionReadSchemaDataType) {
  updatedClienteRef.value = cliente;
}

function handleChangeCliente() {
  emit('changeCliente');
}

function setObjetoFormData(value: typeof objetoFormData.value) {
  objetoFormData.value = value;
}

function setObjetoDados(value: Record<string, unknown>) {
  objetoDados.value = value;
}

function setOsDados(value: Record<string, unknown>) {
  osDados.value = value;
}

const {
  isHistoricoModalOpen,
  openHistoricoModal,
  closeHistoricoModal,
  reutilizarObjeto,
} = useOSClientHistory({ setObjetoFormData });

function setSelectedHistorico(value: string) {
  selectedHistorico.value = value;
}

function closeObjetoModal() {
  isObjetoSelectModalOpen.value = false;
}

const formErrors = computed<Record<string, string | undefined>>(() => {
  if (isCreateMode.value) {
    if (form.criar.submitCount.value === 0) return {};
    return { ...form.criar.errors.value };
  }
  return {
    ...form.atualizarGeral.errors.value,
    ...form.atualizarObjeto.errors.value,
  };
});

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
  isDiagnosticoLocked,
  isItemsLocked,
  creditoAoReabrir,
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
  displayValorAcrescimo,
  formErrors,
  objetoFormData,
  objetoDados,
  osDados,
  objetosHistorico,
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
  isObjetoSelectModalOpen,
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
  handleValorEntregaUpdate,
  handleUsarCredito,
  saldoCreditoCliente,
  setObjetoFormData,
  setObjetoDados,
  setOsDados,
  setSelectedHistorico,
  applyObjetoHistorico,
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
  closeObjetoModal,
  handleObjetoSelected,
  isHistoricoModalOpen,
  openHistoricoModal,
  closeHistoricoModal,
  reutilizarObjeto,
});
</script>

<template>
  <OSFormModalShell />
  <OSFormAuxModals />
  <GerenteAprovacaoModal
    :is-open="gerenteReopen.isOpen.value"
    :is-loading="gerenteReopen.isLoading.value"
    @confirmar="gerenteReopen.confirmar"
    @cancelar="gerenteReopen.cancelar"
  />
</template>
