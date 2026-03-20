<script setup lang="ts">
import { ref, computed } from 'vue';
import OSTable from '../../ordens/components/OSTable.vue';
import OSFormModal from '../../ordens/components/OSFormModal.vue';
import OSClienteSearchModal from '../../ordens/components/OSClienteSearchModal.vue';
import OSCancelModal from '../../ordens/components/OSCancelModal.vue';
<<<<<<< Updated upstream
import CustomerFormModal from '@/modules/customers/components/modal/CustomerFormModal.vue';
=======
>>>>>>> Stashed changes
import OSStats from '../../ordens/components/OSStats.vue';
import OSPrintTemplate from '../../ordens/components/OSPrintTemplate.vue';
import OSFinalizarModal from '../../ordens/components/OSFinalizarModal.vue';
import OSReopenOptionsModal from '../../ordens/components/form/OSReopenOptionsModal.vue';

import { useOrderServiceQueryAll, useOrderServiceQueryStats } from '../../ordens/composables/request/useOrderServiceGet.queries';
import { getUniqueOS } from '../../ordens/services/orderServiceGet.service';

import type { OrderServiceReadDataType } from '../../ordens/schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';
import type { OsStatusEnumDataType } from '../../ordens/schemas/enums/osEnums.schema';
import { useToast } from '@/shared/composables/useToast';
import { useReopenOrderServiceMutation } from '../../ordens/composables/request/useOrderServiceUpdate.mutate';

const toast = useToast();
const reopenMutation = useReopenOrderServiceMutation();

const {
  searchQuery,
  activeStatusFilterQuery,
  orderServices,
  totalPages,
  totalItems,
  currentPage,
  isLoading,
  isError,
  setPage,
} = useOrderServiceQueryAll();

const { stats, isLoading: isStatsLoading } = useOrderServiceQueryStats();

// ─── Estado dos modais ────────────────────────────────────────────────────────
const isClienteSearchModalOpen = ref(false);
const isFormModalOpen = ref(false);
const isCancelModalOpen = ref(false);

const selectedOS = ref<OrderServiceReadDataType | null>(null);
const selectedCliente = ref<CustomerUnionReadSchemaDataType | null>(null);
const osToCancel = ref<OrderServiceReadDataType | null>(null);
const osToFinalizar = ref<OrderServiceReadDataType | null>(null);
const isFinalizarDirectOpen = ref(false);
const osToReopen = ref<OrderServiceReadDataType | null>(null);
const isReopenDirectOpen = ref(false);

const osToPrint = ref<OrderServiceReadDataType | null>(null);
const printType = ref<'ENTRADA' | 'SAIDA' | 'CANCELAMENTO' | null>(null);

// ─── Filtro de status ─────────────────────────────────────────────────────────
const osActiveFilter = computed<string | null>({
  get: () => activeStatusFilterQuery.value ?? null,
  set: (val: string | null) => {
    activeStatusFilterQuery.value = (val as OsStatusEnumDataType | null) ?? undefined;
  },
});

// ─── Abertura de nova OS ──────────────────────────────────────────────────────
function handleOpenNovaOS() {
  selectedOS.value = null;
  selectedCliente.value = null;
  isClienteSearchModalOpen.value = true;
}

function handleCloseClienteSearch() {
  isClienteSearchModalOpen.value = false;
}

function handleClienteSelected(cliente: CustomerUnionReadSchemaDataType) {
  selectedCliente.value = cliente;
  isClienteSearchModalOpen.value = false;
  isFormModalOpen.value = true;
}

function handleChangeCliente() {
  isFormModalOpen.value = false;
  isClienteSearchModalOpen.value = true;
}

function handleCloseFormModal() {
  isFormModalOpen.value = false;
  selectedOS.value = null;
  selectedCliente.value = null;
}

// ─── Ações da tabela ──────────────────────────────────────────────────────────
async function handleView(os: OrderServiceReadDataType) {
  try {
    selectedOS.value = await getUniqueOS(os.numero_os);
    selectedCliente.value = null;
    isFormModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar detalhes da OS');
  }
}

async function handleEdit(os: OrderServiceReadDataType) {
  try {
    selectedOS.value = await getUniqueOS(os.numero_os);
    selectedCliente.value = null;
    isFormModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar OS para edição');
  }
}

async function handleFinalizar(os: OrderServiceReadDataType) {
  try {
    osToFinalizar.value = await getUniqueOS(os.numero_os);
    isFinalizarDirectOpen.value = true;
  } catch {
    toast.error('Erro ao carregar OS');
  }
}

function handleCloseFinalizarDirect() {
  isFinalizarDirectOpen.value = false;
  osToFinalizar.value = null;
}

async function handleFinalizadoDirect({ shouldPrint }: { shouldPrint: boolean }) {
  if (shouldPrint && osToFinalizar.value) {
    try {
      const osAtualizada = await getUniqueOS(osToFinalizar.value.numero_os);
      osToPrint.value = osAtualizada;
      printType.value = 'SAIDA';
      setTimeout(() => {
        window.print();
        setTimeout(() => {
          osToPrint.value = null;
          printType.value = null;
        }, 500);
      }, 100);
    } catch {
      toast.error('Erro ao preparar impressão');
    }
  }
  handleCloseFinalizarDirect();
}

function handleCancelar(os: OrderServiceReadDataType) {
  osToCancel.value = os;
  isCancelModalOpen.value = true;
}

function handleCloseCancelModal() {
  isCancelModalOpen.value = false;
  osToCancel.value = null;
}

async function handleCancelled({ shouldPrint }: { shouldPrint: boolean }) {
  if (shouldPrint && osToCancel.value) {
    try {
      const osAtualizada = await getUniqueOS(osToCancel.value.numero_os);
      osToPrint.value = osAtualizada;
      printType.value = 'CANCELAMENTO';
      setTimeout(() => {
        window.print();
        setTimeout(() => {
          osToPrint.value = null;
          printType.value = null;
        }, 500);
      }, 100);
    } catch {
      toast.error('Erro ao preparar impressão do cancelamento');
    }
  }
  handleCloseCancelModal();
}

function handleReabrir(os: OrderServiceReadDataType) {
  osToReopen.value = os;
  isReopenDirectOpen.value = true;
}

function handleReopenCancel() {
  isReopenDirectOpen.value = false;
  osToReopen.value = null;
}

function handleReopenTextOnly() {
  if (osToReopen.value?.numero_os) {
    reopenMutation.mutate(osToReopen.value.numero_os);
  }
  isReopenDirectOpen.value = false;
  osToReopen.value = null;
}

function handleReopenFull() {
  if (osToReopen.value?.numero_os) {
    reopenMutation.mutate(osToReopen.value.numero_os);
  }
  isReopenDirectOpen.value = false;
  osToReopen.value = null;
}

async function handlePrintOS(os: OrderServiceReadDataType) {
  try {
    const osCompleta = await getUniqueOS(os.numero_os);
    osToPrint.value = osCompleta;
    printType.value = osCompleta.status === 'CANCELADA' ? 'CANCELAMENTO' : 'SAIDA';
    setTimeout(() => {
      window.print();
      setTimeout(() => {
        osToPrint.value = null;
        printType.value = null;
      }, 500);
    }, 100);
  } catch {
    toast.error('Erro ao preparar impressão');
  }
}

defineExpose({ handleOpenNovaOS });
</script>

<template>
  <div class="space-y-6">
    <OSStats :stats="stats" :loading="isStatsLoading" />

    <div
      v-if="isError"
      class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
    >
      Erro ao carregar ordens de serviço. Verifique sua conexão e tente novamente.
    </div>

    <OSTable
      :ordens-servico="orderServices"
      :is-loading="isLoading"
      v-model:search="searchQuery"
      v-model:active-filter="osActiveFilter"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      @view="handleView"
      @edit="handleEdit"
      @finalizar="handleFinalizar"
      @cancelar="handleCancelar"
      @reabrir="handleReabrir"
      @print="handlePrintOS"
      @update:current-page="setPage"
    />

    <OSClienteSearchModal
      :is-open="isClienteSearchModalOpen"
      @close="handleCloseClienteSearch"
      @select-cliente="handleClienteSelected"
    />

    <OSFormModal
      :is-open="isFormModalOpen"
      :ordem-servico="selectedOS"
      :selected-cliente="selectedCliente"
      @close="handleCloseFormModal"
      @change-cliente="handleChangeCliente"
    />

    <OSCancelModal
      :is-open="isCancelModalOpen"
      :os-numero="osToCancel?.numero_os ?? null"
      :os-display-number="osToCancel?.numero_os"
      @close="handleCloseCancelModal"
      @cancelled="handleCancelled"
    />

    <OSFinalizarModal
      :is-open="isFinalizarDirectOpen"
      :os-numero="osToFinalizar?.numero_os ?? null"
      :ordem-servico="osToFinalizar"
      @close="handleCloseFinalizarDirect"
      @finalized="handleFinalizadoDirect"
    />

    <OSReopenOptionsModal
      :is-open="isReopenDirectOpen"
      @cancel="handleReopenCancel"
      @text-only="handleReopenTextOnly"
      @full="handleReopenFull"
    />

    <OSPrintTemplate
      v-if="osToPrint"
      :ordem-servico="osToPrint"
      :type="printType || 'SAIDA'"
    />

  </div>
</template>
