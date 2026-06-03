<script setup lang="ts">
import OSClientCard from './OSClientCard.vue';
import OSSummaryCard from './OSSummaryCard.vue';
import { useOSFormView } from '../../context/useOSFormView.context';

const view = useOSFormView();
</script>

<template>
  <fieldset :disabled="view.isStructureLocked.value" class="contents lg:block space-y-4">
    <OSSummaryCard
      :itens="view.displayItems.value"
      :subtotal="view.displaySubtotal.value"
      :valor-entrega="view.displayValorEntrega.value"
      :valor-desconto="view.displayValorDesconto.value"
      :valor-total="view.displayValorTotal.value"
      :valor-entrada="view.displayValorEntrada.value"
      :is-locked="view.isStructureLocked.value"
      @update:valor-entrada="view.handleValorEntradaUpdate"
    />

    <OSClientCard
      :cliente="view.currentCliente.value"
      :status="view.currentOSData.value?.status"
      :data-criacao="view.currentOSData.value?.data_criacao"
      :data-finalizacao="view.currentOSData.value?.data_finalizacao"
      :is-edit-mode="view.isEditMode.value"
      :is-finalizada="view.isFinalizada.value"
      @change-cliente="view.handleChangeCliente"
      @update-cliente="view.handleUpdateCliente"
      @open-historico="view.openHistoricoModal"
    />
  </fieldset>
</template>
