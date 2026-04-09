<script setup lang="ts">
import OSClientCard from './OSClientCard.vue';
import OSControlsCard from './OSControlsCard.vue';
import OSSummaryCard from './OSSummaryCard.vue';
import { useOSFormView } from '../../context/useOSFormView.context';

const view = useOSFormView();
</script>

<template>
  <fieldset :disabled="view.isStructureLocked.value" class="contents lg:block space-y-4">
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

    <OSControlsCard
      :status="view.controlsStatus.value"
      :is-create-mode="view.isCreateMode.value"
      :funcionario-id="view.controlsFuncionarioId.value"
      :prioridade="view.controlsPrioridade.value"
      :data-previsao="view.controlsDataPrevisao.value"
      :status-options="view.statusOptions.value"
      :prioridade-options="view.prioridadeOptions.value"
      :funcionarios-options="view.funcionariosOptions.value"
      @update:status="view.handleStatusUpdate"
      @update:funcionario-id="view.handleFuncionarioIdUpdate"
      @update:prioridade="view.handlePrioridadeUpdate"
      @update:data-previsao="view.handleDataPrevisaoUpdate"
    />

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
  </fieldset>
</template>
