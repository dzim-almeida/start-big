<script setup lang="ts">
import OSReopenOptionsModal from './OSReopenOptionsModal.vue';
import OSItemFormModal from './OSItemFormModal.vue';
import OSEquipamentoSelectModal from './OSEquipamentoSelectModal.vue';
import OSClientHistoryModal from './OSClientHistoryModal.vue';
import OSPrintTemplate from '../OSPrintTemplate.vue';
import OSPrintCupom from '../OSPrintCupom.vue';
import OSPrintSelectModal from '../OSPrintSelectModal.vue';
import OSFinalizarModal from '../OSFinalizarModal.vue';
import { useOSFormView } from '../../context/useOSFormView.context';

const view = useOSFormView();
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

  <OSPrintSelectModal
    :is-open="view.isPrintSelectModalOpen.value"
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

  <OSFinalizarModal
    :is-open="view.isFinalizarModalOpen.value"
    :os-numero="view.osNumber.value"
    :ordem-servico="view.currentOSData.value"
    @close="view.closeFinalizarModal"
    @finalized="view.onFinalized"
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
