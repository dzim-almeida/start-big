<script setup lang="ts">
import OSClientCard from './OSClientCard.vue';
import OSSummaryCard from './OSSummaryCard.vue';
import OSNotasCard from './OSNotasCard.vue';
import { useOSFormView } from '../../context/useOSFormView.context';
import { recursoDisponivel } from '@/shared/config/planos';

const view = useOSFormView();
// "Notas desta OS" (M5): só na OS finalizada e para quem tem algum módulo fiscal.
const fiscalDisponivel = recursoDisponivel('nfe') || recursoDisponivel('nfse');
</script>

<template>
  <fieldset :disabled="view.isStructureLocked.value" class="contents lg:block space-y-4">
    <OSSummaryCard
      :subtotal="view.displaySubtotal.value"
      :valor-entrega="view.displayValorEntrega.value"
      :valor-desconto="view.displayValorDesconto.value"
      :valor-total="view.displayValorTotal.value"
      :valor-entrada="view.displayValorEntrada.value"
      :forma-pagamento-entrada-id="view.displayFormaPagamentoEntradaId.value"
      :valor-acrescimo="view.displayValorAcrescimo.value"
      :is-locked="view.isStructureLocked.value"
      :is-finalizada="view.isFinalizada.value"
      :pagamentos="view.currentOSData.value?.pagamentos ?? []"
      :credito-ao-reabrir="view.currentOSData.value?.credito_anterior ?? view.creditoAoReabrir.value"
      :saldo-credito-cliente="view.isCreateMode.value ? view.saldoCreditoCliente.value : 0"
      :status="view.currentOSData.value?.status"
      :situacao-equipamento="view.currentOSData.value?.situacao_equipamento"
      :os-number="view.osNumber.value"
      :data-criacao="view.currentOSData.value?.data_criacao"
      :data-finalizacao="view.currentOSData.value?.data_finalizacao"
      @update:valor-entrada="view.handleValorEntradaUpdate"
      @update:valor-entrega="view.handleValorEntregaUpdate"
      @update:forma-pagamento-entrada-id="view.handleFormaPagamentoEntradaUpdate"
      @usar-credito="view.handleUsarCredito"
    />

    <OSClientCard
      :cliente="view.currentCliente.value"
      :is-edit-mode="view.isEditMode.value"
      :is-locked="view.isStructureLocked.value"
      @change-cliente="view.handleChangeCliente"
      @update-cliente="view.handleUpdateCliente"
      @open-historico="view.openHistoricoModal"
    />
  </fieldset>

  <!-- Fora do fieldset: a OS finalizada trava a estrutura, mas a nota se emite depois. -->
  <div v-if="fiscalDisponivel && view.isFinalizada.value && view.osNumber.value" class="lg:mt-4">
    <OSNotasCard :os-numero="view.osNumber.value" />
  </div>
</template>
