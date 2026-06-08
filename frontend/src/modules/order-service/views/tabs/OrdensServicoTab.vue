<script setup lang="ts">
import { ref, computed } from 'vue';
import OSTable from '../../ordens/components/OSTable.vue';
import OSCancelModal from '../../ordens/components/OSCancelModal.vue';
import OSStats from '../../ordens/components/OSStats.vue';
import OSPrintTemplate from '../../ordens/components/OSPrintTemplate.vue';
import OSPrintCupom from '../../ordens/components/OSPrintCupom.vue';
import PrintFormatSelectModal from '@/shared/components/print/PrintFormatSelectModal.vue';
import OSFinalizarModal, { type DadosFinalizacaoOS } from '../../ordens/components/OSFinalizarModal.vue';
import OSPagamentoModal from '../../ordens/components/OSPagamentoModal.vue';
import OSReopenOptionsModal from '../../ordens/components/form/OSReopenOptionsModal.vue';
import type { PrintFormat } from '../../ordens/composables/modal/useOSPrintFlow';

import { useOrderServiceQueryAll, useOrderServiceQueryStats } from '../../ordens/composables/request/useOrderServiceGet.queries';
import { getUniqueOS } from '../../ordens/services/orderServiceGet.service';

import type { OrderServiceReadDataType } from '../../ordens/schemas/orderServiceQuery.schema';
import type { OsStatusEnumDataType } from '../../ordens/schemas/enums/osEnums.schema';
import { useToast } from '@/shared/composables/useToast';
import { useReopenOrderServiceMutation, useReadyOrderServiceMutation } from '../../ordens/composables/request/useOrderServiceUpdate.mutate';
import { useOSCreateFlow } from '../../ordens/composables/useOSCreateFlow';

const toast = useToast();
const reopenMutation = useReopenOrderServiceMutation();
const finalizarEntregaMutation = useReadyOrderServiceMutation();

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

const { openExistingOS } = useOSCreateFlow();

// ─── Estado dos modais ────────────────────────────────────────────────────────
const isCancelModalOpen = ref(false);

const osToCancel = ref<OrderServiceReadDataType | null>(null);
const osToFinalizar = ref<OrderServiceReadDataType | null>(null);
const isFinalizarDirectOpen = ref(false);
const isPagamentoDirectOpen = ref(false);
const dadosFinalizacaoDirect = ref<DadosFinalizacaoOS | null>(null);
const osToReopen = ref<OrderServiceReadDataType | null>(null);
const isReopenDirectOpen = ref(false);

const creditoAoReabrirDirect = computed(() => {
  const os = osToFinalizar.value;
  if (!os) return null;
  if (os.credito_anterior != null) return os.credito_anterior;
  if (!os.pagamentos?.length) return null;
  const totalPago = os.pagamentos.reduce((s, p) => s + p.valor, 0);
  return Math.min(totalPago, os.valor_total);
});

const osToPrint = ref<OrderServiceReadDataType | null>(null);
const printType = ref<'ENTRADA' | 'SAIDA' | 'CANCELAMENTO' | null>(null);
const printFormat = ref<PrintFormat>('A4');
const isPrintSelectOpen = ref(false);
const pendingPrintAfterSelect = ref<(() => void) | null>(null);

// ─── Filtro de status ─────────────────────────────────────────────────────────
const osActiveFilter = computed<string | null>({
  get: () => activeStatusFilterQuery.value ?? null,
  set: (val: string | null) => {
    activeStatusFilterQuery.value = (val as OsStatusEnumDataType | null) ?? undefined;
  },
});

// ─── Ações da tabela ──────────────────────────────────────────────────────────
async function handleView(os: OrderServiceReadDataType) {
  try {
    const osCompleta = await getUniqueOS(os.numero_os);
    openExistingOS(osCompleta);
  } catch {
    toast.error('Erro ao carregar detalhes da OS');
  }
}

async function handleEdit(os: OrderServiceReadDataType) {
  try {
    const osCompleta = await getUniqueOS(os.numero_os);
    openExistingOS(osCompleta);
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
  isPagamentoDirectOpen.value = false;
  dadosFinalizacaoDirect.value = null;
  osToFinalizar.value = null;
}

function handleAdvanceDirect(data: DadosFinalizacaoOS) {
  const isEntrega = data.situacao_equipamento === 'SEM_REPARO' || data.situacao_equipamento === 'CONDENADO';

  if (isEntrega) {
    if (!osToFinalizar.value?.numero_os) return;
    finalizarEntregaMutation.mutate(
      {
        osNumber: osToFinalizar.value.numero_os,
        readyOs: {
          situacao_equipamento: data.situacao_equipamento,
          garantia: data.garantia,
          solucao: data.solucao,
          observacoes: data.observacoes ?? '',
          desconto: data.desconto,
          taxa_entrega: osToFinalizar.value?.taxa_entrega ?? 0,
          acrescimo: 0,
          valor_entrada: data.zerarAdiantamento ? 0 : undefined,
          zerar_adiantamento: data.zerarAdiantamento ?? false,
          pagamentos: [],
        },
      },
      {
        onSuccess: async () => {
          await handleFinalizadoDirect({ shouldPrint: data.shouldPrint ?? false });
        },
      },
    );
    return;
  }

  dadosFinalizacaoDirect.value = data;
  isPagamentoDirectOpen.value = true;
}

function handlePagamentoVoltarDirect() {
  isPagamentoDirectOpen.value = false;
}

async function handleFinalizadoDirect({ shouldPrint }: { shouldPrint: boolean }) {
  if (shouldPrint && osToFinalizar.value) {
    try {
      const osAtualizada = await getUniqueOS(osToFinalizar.value.numero_os);
      osToPrint.value = osAtualizada;
      printType.value = 'SAIDA';
      pendingPrintAfterSelect.value = () => handleCloseFinalizarDirect();
      isPrintSelectOpen.value = true;
      return;
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
  const osCancelada = osToCancel.value;
  handleCloseCancelModal();
  if (shouldPrint && osCancelada) {
    try {
      const osAtualizada = await getUniqueOS(osCancelada.numero_os);
      osToPrint.value = osAtualizada;
      printType.value = 'CANCELAMENTO';
      pendingPrintAfterSelect.value = null;
      isPrintSelectOpen.value = true;
    } catch {
      toast.error('Erro ao preparar impressão do cancelamento');
    }
  }
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
    if (osCompleta.status === 'FINALIZADA') {
      printType.value = 'SAIDA';
    } else if (osCompleta.status === 'CANCELADA') {
      printType.value = 'CANCELAMENTO';
    } else {
      printType.value = 'ENTRADA';
    }
    pendingPrintAfterSelect.value = null;
    isPrintSelectOpen.value = true;
  } catch {
    toast.error('Erro ao preparar impressão');
  }
}

function handlePrintFormatSelected(format: PrintFormat) {
  printFormat.value = format;
  isPrintSelectOpen.value = false;

  setTimeout(() => {
    window.print();
    setTimeout(() => {
      pendingPrintAfterSelect.value?.();
      pendingPrintAfterSelect.value = null;
      osToPrint.value = null;
      printType.value = null;
    }, 500);
  }, 100);
}

function handleClosePrintSelect() {
  isPrintSelectOpen.value = false;
  pendingPrintAfterSelect.value = null;
  osToPrint.value = null;
  printType.value = null;
}

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

    <OSCancelModal
      :is-open="isCancelModalOpen"
      :os-numero="osToCancel?.numero_os ?? null"
      :os-display-number="osToCancel?.numero_os"
      :valor-entrada="osToCancel?.valor_entrada ?? 0"
      @close="handleCloseCancelModal"
      @cancelled="handleCancelled"
    />

    <OSFinalizarModal
      :is-open="isFinalizarDirectOpen"
      :os-numero="osToFinalizar?.numero_os ?? null"
      :ordem-servico="osToFinalizar"
      @close="handleCloseFinalizarDirect"
      @advance="handleAdvanceDirect"
    />

    <OSPagamentoModal
      :is-open="isPagamentoDirectOpen"
      :os-numero="osToFinalizar?.numero_os ?? null"
      :ordem-servico="osToFinalizar"
      :dados-os="dadosFinalizacaoDirect"
      :desconto-os="dadosFinalizacaoDirect?.desconto ?? 0"
      :credito-ao-reabrir="creditoAoReabrirDirect"
      @close="handleCloseFinalizarDirect"
      @voltar="handlePagamentoVoltarDirect"
      @finalized="handleFinalizadoDirect"
    />

    <OSReopenOptionsModal
      :is-open="isReopenDirectOpen"
      @cancel="handleReopenCancel"
      @text-only="handleReopenTextOnly"
      @full="handleReopenFull"
    />

    <PrintFormatSelectModal
      :is-open="isPrintSelectOpen"
      subtitle="Selecione o formato desejado para imprimir esta OS."
      @close="handleClosePrintSelect"
      @select="handlePrintFormatSelected"
    />

    <OSPrintTemplate
      v-if="osToPrint && printFormat === 'A4'"
      :ordem-servico="osToPrint"
      :type="printType || 'SAIDA'"
    />

    <OSPrintCupom
      v-if="osToPrint && printFormat === 'CUPOM'"
      :order-service="osToPrint"
      :type="printType || 'SAIDA'"
    />

  </div>
</template>
