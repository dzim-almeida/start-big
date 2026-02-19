<script setup lang="ts">
import { ref, computed, watch } from 'vue';

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
import ServicoFormModal from '../../servicos/components/ServicoFormModal.vue';
import OSItemFormModal from './form/OSItemFormModal.vue';
import OSEquipamentoSelectModal from './form/OSEquipamentoSelectModal.vue';

import type { OrdemServicoRead, OrdemServicoItemCreate } from '../types/ordemServico.types';
import { useServicoModal } from '../../servicos/composables/useServicoModal';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';
import type { ClienteSearchResult } from '@/shared/services/cliente.service';
import { getClientEquipments } from '@/modules/customers/services/cliente.service';

import { useOSForm } from '../composables/useOSForm';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  isOpen: boolean;
  ordemServico?: OrdemServicoRead | null;
  selectedCliente?: ClienteSearchResult | null;
  autoShowReopen?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  changeCliente: [];
  saved: [os: OrdemServicoRead];
}>();

const printType = ref<'ENTRADA' | 'SAIDA'>('ENTRADA');
const isFinalizarModalOpen = ref(false);
const savedOS = ref<OrdemServicoRead | null>(null);

function handlePrint() {
  const os = savedOS.value || props.ordemServico;
  if (!os?.id) return;
  printType.value = 'ENTRADA';
  setTimeout(() => window.print(), 100);
}

function onSaved(os: OrdemServicoRead) {
  if (!props.ordemServico) {
    savedOS.value = os;
    printType.value = 'ENTRADA';
    setTimeout(() => {
      window.print();
      handleClose();
    }, 100);
  } else {
    handleClose();
  }
}

const osForm = useOSForm(props, emit, { onSuccess: onSaved });

const {
  form,
  itens,
  apiError,
  isEditMode,
  servicosOptions,
  produtosOptions,
  funcionariosOptions,
  prioridadeOptions,
  statusOptions,
  subtotal,
  valorDesconto,
  valorTotal,
  isPending,
  isLoadingServicos,
  isLoadingProdutos,
  handleClose,
  handleChangeCliente,
  handleSubmit,
  removeItem,
  reopenOS,
} = osForm;

const isItemModalOpen = ref(false);
const editingItemIndex = ref<number | null>(null);
const editingItem = ref<OrdemServicoItemCreate | null>(null);
const { openCreateModal: openCreateServicoModal } = useServicoModal();

function openAddItemModal() {
  editingItemIndex.value = null;
  editingItem.value = null;
  isItemModalOpen.value = true;
}

function openEditItemModal(index: number) {
  editingItemIndex.value = index;
  editingItem.value = {
    ...itens.value[index],
    servico_id: itens.value[index].servico_id ? Number(itens.value[index].servico_id) : undefined,
  } as OrdemServicoItemCreate;
  isItemModalOpen.value = true;
}

function closeItemModal() {
  isItemModalOpen.value = false;
  editingItem.value = null;
  editingItemIndex.value = null;
}

function handleSaveItem(item: OrdemServicoItemCreate) {
  const formItem = {
    ...item,
    servico_id: item.servico_id ? String(item.servico_id) : undefined,
  };
  if (editingItemIndex.value !== null) {
    itens.value[editingItemIndex.value] = formItem;
  } else {
    itens.value.push(formItem);
  }
}

type TabType = 'equipamento' | 'diagnostico' | 'servicos';
const activeTab = ref<TabType>('equipamento');

const tabs: { id: TabType; label: string }[] = [
  { id: 'equipamento', label: 'Equipamento' },
  { id: 'diagnostico', label: 'Diagnostico' },
  { id: 'servicos', label: 'Serviços e Peças' },
];

const nextOSNumber = ref<string | null>(null);

const osNumber = computed(() => {
  const num = props.ordemServico?.numero || nextOSNumber.value;
  return num ? String(num).replace(/^OS-\d{4}-/, '') : '...';
});

const currentCliente = computed(() => props.selectedCliente || props.ordemServico?.cliente);

const equipamentoFormData = computed({
  get: () => ({
    equipamento: form.value.equipamento,
    marca: form.value.marca,
    modelo: form.value.modelo,
    numero_serie: form.value.numero_serie,
    imei: form.value.imei,
    cor: form.value.cor,
    senha_aparelho: form.value.senha_aparelho,
    acessorios: form.value.acessorios,
    defeito_relatado: form.value.defeito_relatado,
    condicoes_aparelho: form.value.condicoes_aparelho,
  }),
  set: (val) => Object.assign(form.value, val),
});

const displayOS = computed(() => savedOS.value || props.ordemServico);
const isFinalizada = computed(() => props.ordemServico?.status === 'FINALIZADA');

const isReopenOptionsOpen = ref(false);
const reopenMode = ref<'NONE' | 'TEXT_ONLY' | 'FULL'>('NONE');
const preservedFinalizationDate = ref<string | undefined>(undefined);

const isStructureLocked = computed(() => isFinalizada.value && reopenMode.value === 'NONE');
const isItemsLocked = computed(() => isFinalizada.value || reopenMode.value === 'TEXT_ONLY');

function handleReopenClick() { isReopenOptionsOpen.value = true; }

function handleReopenCancel() {
  isReopenOptionsOpen.value = false;
  reopenMode.value = 'NONE';
}

function handleReopenTextOnly() {
  preservedFinalizationDate.value = form.value.data_finalizacao;
  reopenMode.value = 'TEXT_ONLY';
  isReopenOptionsOpen.value = false;
  reopenOS();
}

function handleReopenFull() {
  reopenMode.value = 'FULL';
  isReopenOptionsOpen.value = false;
  reopenOS();
}

function handleFinalizarOS() { isFinalizarModalOpen.value = true; }

function handleReprintExit() {
  savedOS.value = props.ordemServico || null;
  printType.value = 'SAIDA';
  handlePrint();
}

function handleLocalSubmit() {
  if (reopenMode.value === 'TEXT_ONLY') {
    form.value.status = 'FINALIZADA';
    if (preservedFinalizationDate.value) {
      form.value.data_finalizacao = preservedFinalizationDate.value;
    }
  }
  handleSubmit();
}

function onFinalized({ os, shouldPrint }: { os: OrdemServicoRead; shouldPrint: boolean }) {
  savedOS.value = os;
  if (shouldPrint) {
    printType.value = 'SAIDA';
    handlePrint();
  }
  handleClose();
}

async function handlePhotoChange() {
  if (props.ordemServico?.id) {
    const { ordemServicoService } = await import('../services/ordemServico.service');
    const osUpdated = await ordemServicoService.getById(props.ordemServico.id);
    savedOS.value = osUpdated;
    emit('saved', osUpdated);
  }
}

watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    if (props.autoShowReopen && props.ordemServico?.status === 'FINALIZADA') {
      isReopenOptionsOpen.value = true;
    }
    if (!props.ordemServico?.id) {
      try {
        const { ordemServicoService } = await import('../services/ordemServico.service');
        const res = await ordemServicoService.getNextNumber();
        nextOSNumber.value = res.numero;
      } catch {
        nextOSNumber.value = null;
      }
    }
  } else {
    nextOSNumber.value = null;
    isReopenOptionsOpen.value = false;
    reopenMode.value = 'NONE';
  }
}, { immediate: true });

watch(() => props.ordemServico?.status, (newStatus, oldStatus) => {
  if (oldStatus === 'FINALIZADA' && newStatus === 'EM_ANDAMENTO' && reopenMode.value === 'FULL') {
    form.value.status = 'EM_ANDAMENTO';
    form.value.data_finalizacao = undefined;
  }
});

const equipamentosHistorico = ref<EquipamentoHistorico[]>([]);
const selectedHistorico = ref<string>('');
const isEquipSelectModalOpen = ref(false);

async function fetchEquipamentosHistorico() {
  const clienteId = props.selectedCliente?.id || props.ordemServico?.cliente_id;
  if (!clienteId) {
    equipamentosHistorico.value = [];
    return;
  }
  try {
    const history = await getClientEquipments(clienteId);
    equipamentosHistorico.value = history;
    if (history.length > 0 && !props.ordemServico?.id && !form.value.equipamento) {
      isEquipSelectModalOpen.value = true;
    }
  } catch {
    // Equipment history is optional
  }
}

watch(() => [props.selectedCliente?.id, props.ordemServico?.cliente_id], fetchEquipamentosHistorico, { immediate: true });

function handleEquipamentoSelected(equip: EquipamentoHistorico) {
  form.value.equipamento = equip.equipamento;
  form.value.marca = equip.marca || '';
  form.value.modelo = equip.modelo || '';
  form.value.numero_serie = equip.numero_serie || '';
  const idx = equipamentosHistorico.value.findIndex(
    e => e.numero_serie === equip.numero_serie && e.equipamento === equip.equipamento,
  );
  if (idx !== -1) selectedHistorico.value = String(idx);
  isEquipSelectModalOpen.value = false;
}

function applyEquipamentoHistorico() {
  if (!selectedHistorico.value) return;
  const index = parseInt(selectedHistorico.value);
  const equip = equipamentosHistorico.value[index];
  if (equip) handleEquipamentoSelected(equip);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="" size="3xl" @close="handleClose">
    <template #header>
      <OSFormHeader
        :os-number="osNumber"
        :os-id="props.ordemServico?.id"
        :is-finalizada="isFinalizada"
        :is-pending="isPending"
        :reopen-mode="reopenMode"
        @print="handlePrint"
        @reprint-exit="handleReprintExit"
        @reopen="handleReopenClick"
        @save="handleLocalSubmit"
        @close="handleClose"
      />
    </template>

    <div
      v-if="apiError"
      class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 font-medium"
    >
      {{ apiError }}
    </div>

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
          />
          <OSControlsCard
            :status="form.status"
            :funcionario-id="form.funcionario_id"
            :prioridade="form.prioridade"
            :data-previsao="form.data_previsao"
            :status-options="statusOptions"
            :prioridade-options="prioridadeOptions"
            :funcionarios-options="funcionariosOptions"
            @update:status="form.status = $event"
            @update:funcionario-id="form.funcionario_id = $event"
            @update:prioridade="form.prioridade = $event"
            @update:data-previsao="form.data_previsao = $event"
          />
        </div>
      </fieldset>

      <div class="border-b border-slate-200">
        <nav class="flex gap-0">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            :class="[
              'px-5 py-3 text-sm font-bold transition-all border-b-2 -mb-px',
              activeTab === tab.id
                ? 'text-slate-900 border-blue-600'
                : 'text-slate-400 border-transparent hover:text-slate-600',
            ]"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>
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
            :diagnostico="form.diagnostico"
            :os-id="displayOS?.id"
            :fotos="displayOS?.fotos || []"
            :is-locked="isStructureLocked"
            @update:diagnostico="form.diagnostico = $event"
            @photo-change="handlePhotoChange"
          />

          <OSServicesTab
            v-if="activeTab === 'servicos'"
            :itens="itens"
            :servicos-options="servicosOptions"
            :produtos-options="produtosOptions"
            :is-loading-servicos="isLoadingServicos"
            :is-loading-produtos="isLoadingProdutos"
            :is-locked="isItemsLocked"
            :subtotal="subtotal"
            :valor-desconto="valorDesconto"
            :valor-total="valorTotal"
            :valor-entrada="form.valor_entrada"
            @add-item="openAddItemModal"
            @edit-item="openEditItemModal"
            @remove-item="removeItem"
          />
        </div>
      </fieldset>
    </form>

    <template #footer>
      <OSFormFooter
        :valor-total="valorTotal"
        :is-finalizada="isFinalizada"
        :is-edit-mode="isEditMode"
        :reopen-mode="reopenMode"
        @finalizar="handleFinalizarOS"
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
    v-if="savedOS || props.ordemServico"
    :ordem-servico="(savedOS || props.ordemServico) || null"
    :type="printType"
  />

  <OSFinalizarModal
    v-if="props.ordemServico"
    :is-open="isFinalizarModalOpen"
    :ordem-servico="props.ordemServico"
    :valor-total="valorTotal"
    @close="isFinalizarModalOpen = false"
    @finalized="onFinalized"
  />

  <OSItemFormModal
    :is-open="isItemModalOpen"
    :item="editingItem"
    :servicos-options="servicosOptions"
    :produtos-options="produtosOptions"
    :is-loading-servicos="isLoadingServicos"
    :is-loading-produtos="isLoadingProdutos"
    @close="closeItemModal"
    @save="handleSaveItem"
    @create-new-service="openCreateServicoModal"
  />

  <ServicoFormModal />

  <OSEquipamentoSelectModal
    :is-open="isEquipSelectModalOpen"
    :equipamentos="equipamentosHistorico"
    @close="isEquipSelectModalOpen = false"
    @select="handleEquipamentoSelected"
  />
</template>
