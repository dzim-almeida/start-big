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
      :valor-acrescimo="view.displayValorAcrescimo.value"
      :is-locked="view.isStructureLocked.value"
      :is-finalizada="view.isFinalizada.value"
      :pagamentos="view.currentOSData.value?.pagamentos ?? []"
      :credito-ao-reabrir="view.currentOSData.value?.credito_anterior ?? view.creditoAoReabrir.value"
      :saldo-credito-cliente="view.saldoCreditoCliente.value"
      @update:valor-entrada="view.handleValorEntradaUpdate"
      @update:valor-entrega="view.handleValorEntregaUpdate"
      @usar-credito="view.handleUsarCredito"
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
