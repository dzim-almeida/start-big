<script setup lang="ts">
import { ref, computed, watch, type Component } from 'vue';
import { Smartphone, ClipboardList, Package } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import OSFormHeader from './form/OSFormHeader.vue';
import OSFormFooter from './form/OSFormFooter.vue';
import OSClientCard from './form/OSClientCard.vue';
import OSControlsCard from './form/OSControlsCard.vue';
import OSEquipmentTab from './form/OSEquipmentTab.vue';
import OSDiagnosticoTab from './form/OSDiagnosticoTab.vue';
import OSServicesTab from './form/OSServicesTab.vue';
import OSReopenOptionsModal from './form/OSReopenOptionsModal.vue';
import OSPrintTemplate from './OSPrintTemplate.vue';
import OSFinalizarModal from './OSFinalizarModal.vue';
import OSItemFormModal from './form/OSItemFormModal.vue';
import OSEquipamentoSelectModal from './form/OSEquipamentoSelectModal.vue';

import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { OsItemCreateSchemaDataType } from '../schemas/relationship/osItem.schema';
import type { OsStatusEnumDataType, OsPriorityEnumDataType } from '../schemas/enums/osEnums.schema';
import type { CustomerUnionReadSchemaDataType } from '../schemas/relationship/customer/customer.schema';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';

import { getClientEquipments } from '@/modules/customers/services/customerGet.service';
import { getUniqueOS } from '../services/orderServiceGet.service';

import { useOSFormProvider, useOSFormPendingState } from '../context/useForm.context';
import { useOsEmployeesGet } from '../composables/request/relationship/useOSRelationshipGet.queries';
import { useCreateItemOSMutation } from '../composables/request/useOrderServiceCreate.mutate';
import { useReopenOrderServiceMutation } from '../composables/request/useOrderServiceUpdate.mutate';
import { useOrderServiceDeleteItem } from '../composables/request/useOrderServiceDelete.mutate';

import { OS_STATUS_OPTIONS, OS_PRIORIDADE_OPTIONS } from '../constants/ordemServico.constants';

interface EquipamentoForm {
  equipamento: string;
  marca: string;
  modelo: string;
  numero_serie: string;
  imei: string;
  cor: string;
  senha_aparelho: string;
  acessorios: string;
  defeito_relatado: string;
  condicoes_aparelho: string;
}

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

// ─── 1. PROVIDER (deve ser chamado antes de qualquer await) ───────────────────
const osNumber = computed(() => props.ordemServico?.numero_os ?? null);
const isCreateMode = computed(() => !props.ordemServico);
const savedOS = ref<OrderServiceReadDataType | null>(null);
const printType = ref<'ENTRADA' | 'SAIDA'>('ENTRADA');

const form = useOSFormProvider({
  osNumber,
  isCreateMode,
  onCreateSuccess: (os) => {
    savedOS.value = os;
    printType.value = 'ENTRADA';
    setTimeout(() => {
      window.print();
      handleClose();
    }, 100);
  },
  onUpdateSuccess: () => handleClose(),
  onItemSuccess: () => closeItemModal(),
  onFinalizarSuccess: () => { isFinalizarModalOpen.value = false; },
});

const isPending = useOSFormPendingState(form);

// ─── 2. Estado derivado ───────────────────────────────────────────────────────
const isEditMode = computed(() => !isCreateMode.value);
const isFinalizada = computed(() => props.ordemServico?.status === 'FINALIZADA');
const isCancelada = computed(() => props.ordemServico?.status === 'CANCELADA');
const isLocked = computed(() => isFinalizada.value || isCancelada.value);
const displayOS = computed(() => savedOS.value ?? props.ordemServico ?? null);
const latestOSData = ref<OrderServiceReadDataType | null>(null);
const effectiveOS = computed(() => latestOSData.value ?? props.ordemServico ?? null);

// ─── 3. Employees + Options ───────────────────────────────────────────────────
const employeesQuery = useOsEmployeesGet();
const funcionariosOptions = computed<SelectOption[]>(() => {
  const raw = employeesQuery.data.value as unknown;
  const list = Array.isArray(raw) ? (raw as { id: number; nome: string }[]) : [];
  return [
    { value: '', label: '-- Selecione --' },
    ...list.map(e => ({ value: String(e.id), label: e.nome })),
  ];
});

const statusOptions = OS_STATUS_OPTIONS.map(o => ({ value: o.value, label: o.label })) as SelectOption[];
const prioridadeOptions = OS_PRIORIDADE_OPTIONS.map(o => ({ value: o.value, label: o.label })) as SelectOption[];

// ─── 4. Reopen ────────────────────────────────────────────────────────────────
const reopenMutation = useReopenOrderServiceMutation();
const isReopenOptionsOpen = ref(false);
const reopenMode = ref<'NONE' | 'TEXT_ONLY' | 'FULL'>('NONE');
const preservedFinalizationDate = ref<string | undefined>(undefined);
const isStructureLocked = computed(() => isLocked.value && reopenMode.value === 'NONE');
const isItemsLocked = computed(() => isLocked.value || reopenMode.value === 'TEXT_ONLY');

function handleReopenClick() { isReopenOptionsOpen.value = true; }
function handleReopenCancel() {
  isReopenOptionsOpen.value = false;
  reopenMode.value = 'NONE';
}
function handleReopenTextOnly() {
  preservedFinalizationDate.value = form.atualizarGeral.data_previsao.value;
  reopenMode.value = 'TEXT_ONLY';
  isReopenOptionsOpen.value = false;
  if (osNumber.value) reopenMutation.mutate(osNumber.value);
}
function handleReopenFull() {
  reopenMode.value = 'FULL';
  isReopenOptionsOpen.value = false;
  if (osNumber.value) reopenMutation.mutate(osNumber.value);
}

// ─── 5. Tabs ──────────────────────────────────────────────────────────────────
type TabType = 'equipamento' | 'diagnostico' | 'servicos';
const activeTab = ref<TabType>('equipamento');

const tabs: { id: TabType; label: string; icon: Component }[] = [
  { id: 'equipamento', label: 'Equipamento',     icon: Smartphone    },
  { id: 'diagnostico', label: 'Diagnóstico',      icon: ClipboardList },
  { id: 'servicos',    label: 'Serviços e Peças', icon: Package       },
];

// ─── 6. Itens ─────────────────────────────────────────────────────────────────
const addItemMutation = useCreateItemOSMutation();
const deleteItemMutation = useOrderServiceDeleteItem();

const isItemModalOpen = ref(false);
const editingItemIndex = ref<number | null>(null);
const editingItem = ref<OsItemCreateSchemaDataType | null>(null);
const editingItemId = ref<number | null>(null);

const displayItems = computed(() =>
  isCreateMode.value
    ? form.criar.itens.value.map(e => e.value)
    : (effectiveOS.value?.itens ?? [])
);

function openAddItemModal() {
  editingItemIndex.value = null;
  editingItem.value = null;
  editingItemId.value = null;
  isItemModalOpen.value = true;
}

function openEditItemModal(index: number) {
  const item = displayItems.value[index];
  if (!item) return;
  editingItemIndex.value = index;
  editingItemId.value = 'id' in item ? (item as { id: number }).id : null;
  editingItem.value = {
    tipo: item.tipo,
    nome: item.nome,
    unidade_medida: item.unidade_medida,
    quantidade: item.quantidade,
    valor_unitario: item.valor_unitario,
  };
  isItemModalOpen.value = true;
}

function closeItemModal() {
  isItemModalOpen.value = false;
  editingItem.value = null;
  editingItemIndex.value = null;
  editingItemId.value = null;
}

function handleSaveItem(item: OsItemCreateSchemaDataType) {
  if (isCreateMode.value) {
    if (editingItemIndex.value !== null) {
      form.criar.handleUpdateItem(editingItemIndex.value, item);
    } else {
      form.criar.handleAddItem(item);
    }
    closeItemModal();
  } else {
    if (editingItemId.value !== null) {
      form.item.setEditingItem(editingItemId.value, item);
      form.item.onSubmit();
      // closeItemModal chamado via onItemSuccess; re-fetch para atualizar itens
      if (osNumber.value) {
        getUniqueOS(osNumber.value).then(os => { latestOSData.value = os; });
      }
    } else if (osNumber.value) {
      addItemMutation.mutate(
        { osNumber: osNumber.value, osItem: item },
        { onSuccess: (data) => { latestOSData.value = data; closeItemModal(); } },
      );
    }
  }
}

function handleRemoveItem(index: number) {
  if (isCreateMode.value) {
    form.criar.handleRemoveItem(index);
  } else {
    const item = displayItems.value[index] as { id?: number };
    if (item?.id && osNumber.value) {
      const osNum = osNumber.value;
      deleteItemMutation.mutate(
        { osNumber: osNum, itemOsId: item.id },
        { onSuccess: () => { getUniqueOS(osNum).then(os => { latestOSData.value = os; }); } },
      );
    }
  }
}

// ─── 7. Financeiros ───────────────────────────────────────────────────────────
const displaySubtotal = computed(() => {
  if (isCreateMode.value) {
    return form.criar.itens.value.reduce(
      (sum, e) => sum + e.value.quantidade * e.value.valor_unitario,
      0,
    );
  }
  return (effectiveOS.value?.itens ?? []).reduce((sum, i) => sum + i.valor_total, 0);
});

const displayValorDesconto = computed(() => {
  if (isCreateMode.value) return form.criar.desconto.value ?? 0;
  return effectiveOS.value?.desconto ?? 0;
});

const displayValorTotal = computed(() => {
  if (isCreateMode.value) return Math.max(0, displaySubtotal.value - displayValorDesconto.value);
  return effectiveOS.value?.valor_total ?? 0;
});

// ─── 8. Print ─────────────────────────────────────────────────────────────────
function handlePrint() {
  printType.value = 'ENTRADA';
  setTimeout(() => window.print(), 100);
}

function handleReprintExit() {
  printType.value = 'SAIDA';
  setTimeout(() => window.print(), 100);
}

// ─── 9. Finalizar ─────────────────────────────────────────────────────────────
const isFinalizarModalOpen = ref(false);

function handleFinalizarOS() { isFinalizarModalOpen.value = true; }

function onFinalized({ shouldPrint }: { shouldPrint: boolean }) {
  isFinalizarModalOpen.value = false;
  if (shouldPrint) handleReprintExit();
  handleClose();
}

// ─── 10. Submit ───────────────────────────────────────────────────────────────
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

// ─── 11. Close ────────────────────────────────────────────────────────────────
function handleClose() {
  form.criar.resetForm();
  form.atualizarGeral.resetForm();
  form.atualizarEquipamento.resetForm();
  form.item.resetForm();
  reopenMode.value = 'NONE';
  isReopenOptionsOpen.value = false;
  savedOS.value = null;
  latestOSData.value = null;
  updatedClienteRef.value = null;
  emit('close');
}

function handleChangeCliente() { emit('changeCliente'); }

// ─── 12. Populate ao abrir ────────────────────────────────────────────────────
function populateEditForm(os: OrderServiceReadDataType) {
  form.atualizarGeral.populateForm(os);
  // Converter data ISO para YYYY-MM-DD (BaseInput type="date")
  if (os.data_previsao) {
    form.atualizarGeral.data_previsao.value = os.data_previsao.split('T')[0];
  }
  form.atualizarEquipamento.populateForm({
    tipo_equipamento: os.equipamento.tipo_equipamento,
    marca: os.equipamento.marca,
    modelo: os.equipamento.modelo,
    numero_serie: os.equipamento.numero_serie,
    imei: os.equipamento.imei,
    cor: os.equipamento.cor,
    cliente_id: os.equipamento.cliente_id,
  });
}

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    activeTab.value = 'equipamento';
    if (props.ordemServico) {
      populateEditForm(props.ordemServico);
    } else {
      form.criar.resetForm();
    }
  } else {
    reopenMode.value = 'NONE';
    isReopenOptionsOpen.value = false;
    savedOS.value = null;
  }
}, { immediate: true });

watch(() => props.ordemServico?.status, (newStatus, oldStatus) => {
  if ((oldStatus === 'FINALIZADA' || oldStatus === 'CANCELADA') && newStatus === 'EM_ANDAMENTO' && reopenMode.value === 'FULL') {
    form.atualizarGeral.status.value = 'EM_ANDAMENTO';
  }
});

watch(() => props.selectedCliente, (cliente) => {
  if (cliente && isCreateMode.value) {
    form.criar.cliente_id.value = (cliente as { id?: number }).id;
  }
}, { immediate: true });

// ─── 13. Equipamento histórico ────────────────────────────────────────────────
const equipamentosHistorico = ref<EquipamentoHistorico[]>([]);
const selectedHistorico = ref<string>('');
const isEquipSelectModalOpen = ref(false);

async function fetchEquipamentosHistorico() {
  const clienteId =
    (props.selectedCliente as { id?: number } | null)?.id ??
    (props.ordemServico?.cliente as { id?: number } | null)?.id;
  if (!clienteId) { equipamentosHistorico.value = []; return; }
  try {
    const history = await getClientEquipments(clienteId);
    equipamentosHistorico.value = history;
    if (history.length > 0 && !props.ordemServico && !form.criar.equipamento_tipo_equipamento.value) {
      isEquipSelectModalOpen.value = true;
    }
  } catch {
    // histórico de equipamentos é opcional
  }
}

watch(
  () => [
    (props.selectedCliente as { id?: number } | null)?.id,
    (props.ordemServico?.cliente as { id?: number } | null)?.id,
  ],
  fetchEquipamentosHistorico,
  { immediate: true },
);

function handleEquipamentoSelected(equip: EquipamentoHistorico) {
  if (isCreateMode.value) {
    form.criar.equipamento_tipo_equipamento.value = equip.equipamento;
    form.criar.equipamento_marca.value = equip.marca || '';
    form.criar.equipamento_modelo.value = equip.modelo || '';
    form.criar.equipamento_numero_serie.value = equip.numero_serie || '';
  }
  const idx = equipamentosHistorico.value.findIndex(
    e => e.numero_serie === equip.numero_serie && e.equipamento === equip.equipamento,
  );
  if (idx !== -1) selectedHistorico.value = String(idx);
  isEquipSelectModalOpen.value = false;
}

function applyEquipamentoHistorico() {
  if (!selectedHistorico.value) return;
  const equip = equipamentosHistorico.value[parseInt(selectedHistorico.value)];
  if (equip) handleEquipamentoSelected(equip);
}

// ─── 14. Adapter OSEquipmentTab (v-model EquipamentoForm) ────────────────────
const equipamentoFormData = computed<EquipamentoForm>({
  get: () => isCreateMode.value
    ? {
        equipamento:      form.criar.equipamento_tipo_equipamento.value ?? '',
        marca:            form.criar.equipamento_marca.value ?? '',
        modelo:           form.criar.equipamento_modelo.value ?? '',
        numero_serie:     form.criar.equipamento_numero_serie.value ?? '',
        imei:             form.criar.equipamento_imei.value ?? '',
        cor:              form.criar.equipamento_cor.value ?? '',
        senha_aparelho:   form.criar.senha_aparelho.value ?? '',
        acessorios:       form.criar.acessorios.value ?? '',
        defeito_relatado: form.criar.defeito_relatado.value ?? '',
        condicoes_aparelho: form.criar.condicoes_aparelho.value ?? '',
      }
    : {
        equipamento:      form.atualizarEquipamento.tipo_equipamento.value ?? '',
        marca:            form.atualizarEquipamento.marca.value ?? '',
        modelo:           form.atualizarEquipamento.modelo.value ?? '',
        numero_serie:     form.atualizarEquipamento.numero_serie.value ?? '',
        imei:             form.atualizarEquipamento.imei.value ?? '',
        cor:              form.atualizarEquipamento.cor.value ?? '',
        senha_aparelho:   form.atualizarGeral.senha_aparelho.value ?? '',
        acessorios:       form.atualizarGeral.acessorios.value ?? '',
        defeito_relatado: form.atualizarGeral.defeito_relatado.value ?? '',
        condicoes_aparelho: form.atualizarGeral.condicoes_aparelho.value ?? '',
      },
  set: (val: EquipamentoForm) => {
    if (isCreateMode.value) {
      form.criar.equipamento_tipo_equipamento.value = val.equipamento;
      form.criar.equipamento_marca.value = val.marca;
      form.criar.equipamento_modelo.value = val.modelo;
      form.criar.equipamento_numero_serie.value = val.numero_serie;
      form.criar.equipamento_imei.value = val.imei;
      form.criar.equipamento_cor.value = val.cor;
      form.criar.senha_aparelho.value = val.senha_aparelho;
      form.criar.acessorios.value = val.acessorios;
      form.criar.defeito_relatado.value = val.defeito_relatado;
      form.criar.condicoes_aparelho.value = val.condicoes_aparelho;
    } else {
      form.atualizarEquipamento.tipo_equipamento.value = val.equipamento;
      form.atualizarEquipamento.marca.value = val.marca;
      form.atualizarEquipamento.modelo.value = val.modelo;
      form.atualizarEquipamento.numero_serie.value = val.numero_serie;
      form.atualizarEquipamento.imei.value = val.imei;
      form.atualizarEquipamento.cor.value = val.cor;
      form.atualizarGeral.senha_aparelho.value = val.senha_aparelho;
      form.atualizarGeral.acessorios.value = val.acessorios;
      form.atualizarGeral.defeito_relatado.value = val.defeito_relatado;
      form.atualizarGeral.condicoes_aparelho.value = val.condicoes_aparelho;
    }
  },
});

// ─── 15. Bindings do OSControlsCard ──────────────────────────────────────────
const controlsStatus = computed<OsStatusEnumDataType>(() =>
  isCreateMode.value
    ? 'ABERTA'
    : (form.atualizarGeral.status.value as OsStatusEnumDataType | undefined) ?? 'ABERTA'
);

const controlsFuncionarioId = computed<string>(() =>
  isCreateMode.value
    ? String(form.criar.funcionario_id.value ?? '')
    : String(form.atualizarGeral.funcionario_id.value ?? '')
);

const controlsPrioridade = computed<OsPriorityEnumDataType>(() =>
  isCreateMode.value
    ? (form.criar.prioridade.value as OsPriorityEnumDataType | undefined) ?? 'NORMAL'
    : (form.atualizarGeral.prioridade.value as OsPriorityEnumDataType | undefined) ?? 'NORMAL'
);

const controlsDataPrevisao = computed<string>(() =>
  isCreateMode.value
    ? (form.criar.data_previsao.value ?? '')
    : (form.atualizarGeral.data_previsao.value ?? '')
);

function handleStatusUpdate(value: OsStatusEnumDataType) {
  if (!isCreateMode.value) form.atualizarGeral.status.value = value;
}
function handleFuncionarioIdUpdate(value: string) {
  const num = Number(value) || undefined;
  if (isCreateMode.value) form.criar.funcionario_id.value = num;
  else form.atualizarGeral.funcionario_id.value = num;
}
function handlePrioridadeUpdate(value: OsPriorityEnumDataType) {
  if (isCreateMode.value) form.criar.prioridade.value = value;
  else form.atualizarGeral.prioridade.value = value;
}
function handleDataPrevisaoUpdate(value: string) {
  if (isCreateMode.value) form.criar.data_previsao.value = value;
  else form.atualizarGeral.data_previsao.value = value;
}

// ─── 16. Bindings do OSDiagnosticoTab ────────────────────────────────────────
const currentDiagnostico = computed<string>(() =>
  isCreateMode.value
    ? (form.criar.diagnostico.value ?? '')
    : (form.atualizarGeral.diagnostico.value ?? '')
);

function handleDiagnosticoUpdate(value: string) {
  if (isCreateMode.value) form.criar.diagnostico.value = value;
  else form.atualizarGeral.diagnostico.value = value;
}

// ─── 17. Cliente atual ────────────────────────────────────────────────────────
const updatedClienteRef = ref<CustomerUnionReadSchemaDataType | null>(null);

const currentCliente = computed(() =>
  updatedClienteRef.value ?? props.selectedCliente ?? props.ordemServico?.cliente ?? null
);

function handleUpdateCliente(cliente: CustomerUnionReadSchemaDataType) {
  updatedClienteRef.value = cliente;
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="" size="3xl" @close="handleClose">
    <template #header>
      <OSFormHeader
        :os-number="props.ordemServico?.numero_os ?? '...'"
        :is-finalizada="isFinalizada"
        :is-cancelada="isCancelada"
        :is-create-mode="isCreateMode"
        @close="handleClose"
      />
    </template>

    <form class="space-y-4" @submit.prevent="handleLocalSubmit">
      <fieldset :disabled="isStructureLocked" class="contents">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          <OSClientCard
            :cliente="currentCliente"
            :status="props.ordemServico?.status"
            :data-criacao="props.ordemServico?.data_criacao"
            :data-finalizacao="props.ordemServico?.data_finalizacao"
            :is-edit-mode="isEditMode"
            :is-finalizada="isFinalizada"
            @change-cliente="handleChangeCliente"
            @update-cliente="handleUpdateCliente"
          />
          <OSControlsCard
            :status="controlsStatus"
            :funcionario-id="controlsFuncionarioId"
            :prioridade="controlsPrioridade"
            :data-previsao="controlsDataPrevisao"
            :status-options="statusOptions"
            :prioridade-options="prioridadeOptions"
            :funcionarios-options="funcionariosOptions"
            @update:status="handleStatusUpdate"
            @update:funcionario-id="handleFuncionarioIdUpdate"
            @update:prioridade="handlePrioridadeUpdate"
            @update:data-previsao="handleDataPrevisaoUpdate"
          />
        </div>
      </fieldset>

      <div class="flex p-1 mt-2 mb-4 bg-slate-100 rounded-xl gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          @click="activeTab = tab.id"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 px-3 text-sm font-bold rounded-lg transition-all',
            activeTab === tab.id
              ? 'bg-white text-brand-primary shadow-sm'
              : 'text-slate-500 hover:text-slate-700',
          ]"
        >
          <component :is="tab.icon" :size="14" />
          {{ tab.label }}
        </button>
      </div>

      <fieldset :disabled="isStructureLocked" class="contents">
        <div class="min-h-137.5">
          <OSEquipmentTab
            v-if="activeTab === 'equipamento'"
            v-model="equipamentoFormData"
            :equipamentos-historico="equipamentosHistorico"
            :selected-historico="selectedHistorico"
            :is-locked="isStructureLocked"
            @update:selected-historico="selectedHistorico = $event"
            @apply-historico="applyEquipamentoHistorico"
          />

          <OSDiagnosticoTab
            v-if="activeTab === 'diagnostico'"
            :diagnostico="currentDiagnostico"
            :os-numero="displayOS?.numero_os"
            :fotos="displayOS?.fotos ?? []"
            :is-locked="isStructureLocked"
            @update:diagnostico="handleDiagnosticoUpdate"
            @photo-change="() => {}"
          />

          <OSServicesTab
            v-if="activeTab === 'servicos'"
            :itens="displayItems"
            :is-locked="isItemsLocked"
            :subtotal="displaySubtotal"
            :valor-desconto="displayValorDesconto"
            :valor-total="displayValorTotal"
            @add-item="openAddItemModal"
            @edit-item="openEditItemModal"
            @remove-item="handleRemoveItem"
          />
        </div>
      </fieldset>
    </form>

    <template #footer>
      <OSFormFooter
        :valor-total="displayValorTotal"
        :is-finalizada="isFinalizada"
        :is-cancelada="isCancelada"
        :is-edit-mode="isEditMode"
        :is-create-mode="isCreateMode"
        :is-pending="isPending"
        :reopen-mode="reopenMode"
        :os-id="props.ordemServico?.id"
        @finalizar="handleFinalizarOS"
        @print="handlePrint"
        @reprint-exit="handleReprintExit"
        @reopen="handleReopenClick"
        @save="handleLocalSubmit"
      />
    </template>
  </BaseModal>

  <OSReopenOptionsModal
    :is-open="isReopenOptionsOpen"
    @cancel="handleReopenCancel"
    @text-only="handleReopenTextOnly"
    @full="handleReopenFull"
  />

  <OSPrintTemplate
    v-if="displayOS"
    :ordem-servico="displayOS"
    :type="printType"
  />

  <OSFinalizarModal
    :is-open="isFinalizarModalOpen"
    :os-numero="osNumber"
    :ordem-servico="props.ordemServico ?? null"
    @close="isFinalizarModalOpen = false"
    @finalized="onFinalized"
  />

  <OSItemFormModal
    :is-open="isItemModalOpen"
    :item="editingItem"
    @close="closeItemModal"
    @save="handleSaveItem"
  />

  <OSEquipamentoSelectModal
    :is-open="isEquipSelectModalOpen"
    :equipamentos="equipamentosHistorico"
    @close="isEquipSelectModalOpen = false"
    @select="handleEquipamentoSelected"
  />
</template>
