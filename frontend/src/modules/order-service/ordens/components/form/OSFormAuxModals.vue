<script setup lang="ts">
import { ref } from 'vue';

import OSReopenOptionsModal from './OSReopenOptionsModal.vue';
import OSItemFormModal from './OSItemFormModal.vue';
import OSEquipamentoSelectModal from './OSEquipamentoSelectModal.vue';
import OSClientHistoryModal from './OSClientHistoryModal.vue';
import OSPrintTemplate from '../OSPrintTemplate.vue';
import OSPrintCupom from '../OSPrintCupom.vue';
import PrintFormatSelectModal from '@/shared/components/print/PrintFormatSelectModal.vue';
import OSFinalizarModal, { type DadosFinalizacaoOS } from '../OSFinalizarModal.vue';
import OSPagamentoModal from '../OSPagamentoModal.vue';
import { useOSFormView } from '../../context/useOSFormView.context';

const view = useOSFormView();

// ─── Estado do fluxo de finalização (dois modais) ─────────────────────────────
const isPagamentoOpen = ref(false);
const dadosFinalizacao = ref<DadosFinalizacaoOS | null>(null);

function handleAdvance(data: DadosFinalizacaoOS) {
  dadosFinalizacao.value = data;
  isPagamentoOpen.value = true;
}

function handlePagamentoVoltar() {
  isPagamentoOpen.value = false;
}

function handlePagamentoClose() {
  isPagamentoOpen.value = false;
  dadosFinalizacao.value = null;
  view.closeFinalizarModal();
}

function handleFinalized(payload: { shouldPrint: boolean }) {
  isPagamentoOpen.value = false;
  dadosFinalizacao.value = null;
  view.closeFinalizarModal();
  view.onFinalized(payload);
}
</script>

<template>
  <OSClientHistoryModal
    :is-open="view.isHistoricoModalOpen.value"
    :cliente-id="view.currentCliente.value?.id ?? null"
    @close="view.closeHistoricoModal"
    @reutilizar-equipamento="view.reutilizarEquipamento"
  />

  <OSReopenOptionsModal
    :is-open="view.isReopenOptionsOpen.value"
    @cancel="view.handleReopenCancel"
    @text-only="view.handleReopenTextOnly"
    @full="view.handleReopenFull"
  />

  <PrintFormatSelectModal
    :is-open="view.isPrintSelectModalOpen.value"
    subtitle="Selecione o formato desejado para imprimir esta OS."
    @close="view.closePrintSelectModal"
    @select="view.handlePrintFormatSelected"
  />

  <OSPrintTemplate
    v-if="view.currentOSData.value && view.printFormat.value === 'A4'"
    :ordem-servico="view.currentOSData.value"
    :type="view.printType.value"
  />

  <OSPrintCupom
    v-if="view.currentOSData.value && view.printFormat.value === 'CUPOM'"
    :order-service="view.currentOSData.value"
    :type="view.printType.value"
  />

  <!-- Modal 1: Detalhes da finalização -->
  <OSFinalizarModal
    :is-open="view.isFinalizarModalOpen.value"
    :os-numero="view.osNumber.value"
    :ordem-servico="view.currentOSData.value"
    @close="view.closeFinalizarModal"
    @advance="handleAdvance"
  />

  <!-- Modal 2: Pagamento (overlay sobre Modal 1) -->
  <OSPagamentoModal
    :is-open="isPagamentoOpen"
    :os-numero="view.osNumber.value"
    :ordem-servico="view.currentOSData.value"
    :dados-os="dadosFinalizacao"
    :desconto-os="dadosFinalizacao?.desconto ?? 0"
    @close="handlePagamentoClose"
    @voltar="handlePagamentoVoltar"
    @finalized="handleFinalized"
  />

  <OSItemFormModal
    :is-open="view.isItemModalOpen.value"
    :item="view.editingItem.value"
    @close="view.closeItemModal"
    @save="view.handleSaveItem"
  />

  <OSEquipamentoSelectModal
    :is-open="view.isEquipSelectModalOpen.value"
    :equipamentos="view.equipamentosHistorico.value"
    @close="view.closeEquipamentoModal"
    @select="view.handleEquipamentoSelected"
  />
</template>
