<script setup lang="ts">
import { ref, computed } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';
import OSTable from '../../ordens/components/OSTable.vue';
import OSFormModal from '../../ordens/components/OSFormModal.vue';
import OSFinalizarModal from '../../ordens/components/OSFinalizarModal.vue';
import OSClienteSearchModal from '../../ordens/components/OSClienteSearchModal.vue';
import OSCancelModal from '../../ordens/components/OSCancelModal.vue';
import CustomerFormModal from '@/modules/customers/components/CustomerFormModal.vue';
import OSStats from '../../ordens/components/OSStats.vue';
import OSPrintTemplate from '../../ordens/components/OSPrintTemplate.vue';
import { useOrdensServico } from '../../ordens/composables/useOrdensServico';
import { useOSActions } from '../../ordens/composables/useOSActions';
import { ordemServicoService } from '../../ordens/services/ordemServico.service';
import type {
  OrdemServicoRead,
  OrdemServicoListRead,
  OrdemServicoStatus,
} from '../../ordens/types/ordemServico.types';
import type { ClienteSearchResult } from '@/shared/services/cliente.service';
import { useToast } from '@/shared/composables/useToast';

const toast = useToast();
const queryClient = useQueryClient();

const {
  ordensServico,
  stats,
  activeFilterStatus,
  searchQuery,
  isLoading,
  error,
  setFilterStatus,
  currentPage,
  totalPages,
  totalItems,
  setPage,
} = useOrdensServico();

const {
  cancelarMutation,
  isPending: isActionsPending,
} = useOSActions();

const isClienteSearchModalOpen = ref(false);
const isFormModalOpen = ref(false);
const isFinalizarModalOpen = ref(false);
const isCancelModalOpen = ref(false);
const selectedOS = ref<OrdemServicoRead | null>(null);
const selectedCliente = ref<ClienteSearchResult | null>(null);
const osToPrint = ref<OrdemServicoRead | null>(null);
const printType = ref<'ENTRADA' | 'SAIDA' | 'CANCELAMENTO' | null>(null);
const osToCancel = ref<OrdemServicoListRead | null>(null);
const autoShowReopen = ref(false);

const osActiveFilter = computed({
  get: () => activeFilterStatus.value === 'todos' ? null : activeFilterStatus.value as string | null,
  set: (val: string | null) => setFilterStatus((val ?? 'todos') as OrdemServicoStatus | 'todos'),
});

function handleOpenNovaOS() {
  selectedOS.value = null;
  selectedCliente.value = null;
  isClienteSearchModalOpen.value = true;
}

function handleCloseClienteSearch() {
  isClienteSearchModalOpen.value = false;
}

function handleClienteSelected(cliente: ClienteSearchResult) {
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
  autoShowReopen.value = false;
}

function handleCloseFinalizarModal() {
  isFinalizarModalOpen.value = false;
  selectedOS.value = null;
}

async function handleView(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.numero_os);
    selectedOS.value = osCompleta;
    selectedCliente.value = null;
    isFormModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar detalhes da OS');
  }
}

async function handleEdit(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.numero_os);
    selectedOS.value = osCompleta;
    selectedCliente.value = null;
    isFormModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar OS para edicao');
  }
}

async function handleFinalizar(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.numero_os);
    selectedOS.value = osCompleta;
    isFinalizarModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar OS');
  }
}

function handleCancelar(os: OrdemServicoListRead) {
  osToCancel.value = os;
  isCancelModalOpen.value = true;
}

function handleCloseCancelModal() {
  isCancelModalOpen.value = false;
  osToCancel.value = null;
}

function handleConfirmCancel(payload: { motivo: string; print: boolean }) {
  if (osToCancel.value) {
    const osRef = osToCancel.value;
    cancelarMutation.mutate(
      { id: osRef.numero_os, motivo: payload.motivo },
      {
        onSuccess: () => {
          if (payload.print) {
            printCancelamento(osRef, payload.motivo);
          }
          handleCloseCancelModal();
        },
      },
    );
  }
}

async function printCancelamento(os: OrdemServicoListRead, motivo: string) {
  try {
    const osCompleta = await ordemServicoService.getById(os.numero_os);
    const osComMotivo = { ...osCompleta, motivo_cancelamento: motivo };
    osToPrint.value = osComMotivo;
    printType.value = 'CANCELAMENTO';
    setTimeout(() => {
      window.print();
      setTimeout(() => {
        osToPrint.value = null;
        printType.value = null;
        queryClient.invalidateQueries({ queryKey: ['ordens-servico'] });
      }, 500);
    }, 100);
  } catch {
    toast.error('Erro ao preparar impressão do cancelamento');
  }
}

function handleReabrir(os: OrdemServicoListRead) {
  autoShowReopen.value = true;
  handleEdit(os);
}

async function handlePrintOS(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.numero_os);
    osToPrint.value = osCompleta;
    if (osCompleta.status === 'CANCELADA') {
      printType.value = 'CANCELAMENTO';
    } else {
      printType.value = 'SAIDA';
    }
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

defineExpose({
  handleOpenNovaOS,
});
</script>

<template>
  <div class="space-y-6">
    <OSStats :stats="stats" :loading="isLoading" />

    <div
      v-if="error"
      class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
    >
      Erro ao carregar ordens de servico. Verifique sua conexao e tente novamente.
    </div>

    <OSTable
      :ordens-servico="ordensServico"
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
      :auto-show-reopen="autoShowReopen"
      @close="handleCloseFormModal"
      @change-cliente="handleChangeCliente"
      @saved="(os) => selectedOS = os"
    />

    <OSFinalizarModal
      :is-open="isFinalizarModalOpen"
      :ordem-servico="selectedOS"
      @close="handleCloseFinalizarModal"
    />

    <OSCancelModal
      :is-open="isCancelModalOpen"
      :os="osToCancel"
      :is-loading="isActionsPending"
      @close="handleCloseCancelModal"
      @confirm="handleConfirmCancel"
    />

    <OSPrintTemplate
      v-if="osToPrint"
      :ordem-servico="osToPrint"
      :type="printType || 'SAIDA'"
    />

    <CustomerFormModal />
  </div>
</template>
