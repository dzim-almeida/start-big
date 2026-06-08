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
import { useReadyOrderServiceMutation } from '../../composables/request/useOrderServiceUpdate.mutate';

const view = useOSFormView();
const finalizarEntregaMutation = useReadyOrderServiceMutation();

// ─── Estado do fluxo de finalização (dois modais) ─────────────────────────────
const isPagamentoOpen = ref(false);
const dadosFinalizacao = ref<DadosFinalizacaoOS | null>(null);

function handleAdvance(data: DadosFinalizacaoOS) {
  dadosFinalizacao.value = data;

  // Sem reparo / Condenado: finaliza direto sem tela de pagamento
  const isEntrega = data.situacao_equipamento === 'SEM_REPARO' || data.situacao_equipamento === 'CONDENADO';
  if (isEntrega) {
    const osNumber = view.osNumber.value;
    if (!osNumber) return;
    finalizarEntregaMutation.mutate(
      {
        osNumber,
        readyOs: {
          situacao_equipamento: data.situacao_equipamento,
          garantia: data.garantia,
          solucao: data.solucao,
          observacoes: data.observacoes ?? '',
          desconto: data.desconto,
          taxa_entrega: view.currentOSData.value?.taxa_entrega ?? 0,
          acrescimo: 0,
          valor_entrada: data.zerarAdiantamento ? 0 : undefined,
          pagamentos: [],
        },
      },
      {
        onSuccess: () => {
          view.printType.value = 'SAIDA';
          handleFinalized({ shouldPrint: true });
        },
      },
    );
    return;
  }

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
    :credito-ao-reabrir="view.currentOSData.value?.credito_anterior ?? view.creditoAoReabrir.value"
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
