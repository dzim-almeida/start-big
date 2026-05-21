<script setup lang="ts">
import { computed } from 'vue';
import { X, Plus, Info, CheckCircle, TicketX, Trash2 } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';
import { getPaymentDisplayName } from '@/modules/order-service/shared/utils/formatters';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import AddPaymentModal from './AddPaymentModal.vue';

import { useFinishSaleModal } from '../../composables/flows/useFinishSaleModal';
import { useFinishSaleMutation } from '../../composables/mutates/useFinishSaleMutation';
import { usePaymentMethodsQuery } from '../../composables/queries/usePaymentMethodsQuery';
import { useSaleModal } from '../../composables/flows/useSaleModal';

import type { SaleRead } from '../../schemas/sale.schema';
import type { PaymentSaleCreate } from '../../schemas/paymentSale.schema';

const props = defineProps<{
  sale: SaleRead | undefined;
}>();

const saleTotal = computed(() => props.sale?.total ?? 0);

const {
  payments,
  finishModalIsOpen,
  addPaymentModalIsOpen,
  closeFinishModal,
  openAddPaymentModal,
  closeAddPaymentModal,
  addPayment,
  removePayment,
  totalPago,
  troco,
  restante,
  canFinish,
} = useFinishSaleModal(saleTotal);

const finishMutation = useFinishSaleMutation();
const { formasPagamento } = usePaymentMethodsQuery();
const { closeSaleModal } = useSaleModal();

const displaySubtotal = computed(() => formatCurrency(props.sale?.subtotal ?? 0));
const displayDiscount = computed(() => formatCurrency(props.sale?.descontos ?? 0));
const displayDelivery = computed(() => formatCurrency(props.sale?.entrega ?? 0));
const displayTotal = computed(() => formatCurrency(props.sale?.total ?? 0));
const displayTotalPago = computed(() => formatCurrency(totalPago.value));
const displayTroco = computed(() => formatCurrency(troco.value));
const displayRestante = computed(() => formatCurrency(restante.value));

function getPaymentMethodName(formaId: number): string {
  const method = formasPagamento.value.find((fp) => fp.id === formaId);
  return getPaymentDisplayName(method?.nome ?? 'Desconhecido');
}

function handleAddPayment(payment: PaymentSaleCreate) {
  addPayment(payment);
}

function handleRemovePayment(index: number) {
  removePayment(index);
}

function handleFinish() {
  if (!props.sale || !canFinish.value) return;

  finishMutation.mutate(
    { saleId: props.sale.id, payments: payments.value },
    {
      onSuccess: () => {
        closeFinishModal();
        closeSaleModal();
      },
    },
  );
}
</script>

<template>
  <BaseModal :is-open="finishModalIsOpen" title="Finalizar Venda" size="xl">
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-zinc-800">Finalizar Venda</h2>
        </div>

        <button
          type="button"
          class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          @click="closeFinishModal"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <div class="w-full flex flex-col gap-4">
      <div class="p-4 w-full bg-brand-primary/20 rounded-xl">
        <div class="flex items-center gap-5">
          <Info :size="35" class="text-brand-primary" />
          <div class="flex flex-col gap-1">
            <h1 class="font-bold text-sm text-brand-primary">
              Revise os valores da venda e informe as formas de pagamentos
            </h1>
            <p class="font-medium text-xs text-zinc-500">
              Após a finalização da venda, o estoque será baixado e a venda não poderá ser editada.
            </p>
          </div>
        </div>
      </div>

      <div class="w-full border border-zinc-200 rounded-xl flex">
        <div class="p-4 w-1/2 flex flex-col gap-2 border-r border-zinc-200">
          <h1 class="mb-2 font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
            Resumo financeiro
          </h1>
          <div class="flex justify-between items-center">
            <h2 class="font-medium text-sm text-zinc-600">Subtotal dos itens</h2>
            <p class="font-bold text-sm text-zinc-600">{{ displaySubtotal }}</p>
          </div>
          <div class="flex justify-between items-center">
            <h2 class="font-medium text-sm text-zinc-600">Desconto</h2>
            <p class="font-bold text-sm text-red-600">{{ `- ${displayDiscount}` }}</p>
          </div>
          <div class="flex justify-between items-center">
            <h2 class="font-medium text-sm text-zinc-600">Entrega</h2>
            <p class="font-bold text-sm text-green-600">{{ `+ ${displayDelivery}` }}</p>
          </div>
          <div class="mt-auto pt-5 flex items-start justify-between border-t border-zinc-200">
            <h2 class="font-bold text-lg text-zinc-700">Total da Venda</h2>
            <p class="font-bold text-2xl text-zinc-700">{{ displayTotal }}</p>
          </div>
        </div>

        <div class="p-4 flex-1 flex flex-col gap-4">
          <div>
            <h1 class="mb-2 font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
              Restante a pagar
            </h1>
            <p class="font-bold text-3xl" :class="restante > 0 ? 'text-red-600' : 'text-green-600'">
              {{ displayRestante }}
            </p>
          </div>
          <div>
            <h1 class="mb-2 font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
              Troco
            </h1>
            <p class="font-bold text-3xl text-amber-600">{{ displayTroco }}</p>
          </div>
          <div class="p-4 w-full bg-green-200 border border-green-500 rounded-xl">
            <h1 class="mb-2 font-poppins font-bold text-md text-green-700 uppercase tracking-wider">
              <CheckCircle :size="24" class="inline-block mr-2 text-green-700" /> Total Pago
            </h1>
            <p class="font-bold text-3xl text-green-700">{{ displayTotalPago }}</p>
          </div>
        </div>
      </div>

      <div class="p-4 w-full border border-zinc-200 rounded-xl flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <h1 class="mb-2 font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
            Pagamentos
          </h1>
          <BaseButton
            variant="ghost"
            size="sm"
            class="flex items-center gap-2"
            @click="openAddPaymentModal"
          >
            <Plus :size="16" />
            Adicionar pagamento
          </BaseButton>
        </div>
        <section
          class="w-full overflow-hidden rounded-xl border border-zinc-200 bg-white hover:border-brand-primary/30 transition-colors"
        >
          <div class="max-h-[50vh] overflow-y-auto">
            <table class="w-full border-collapse text-sm">
              <thead class="sticky top-0 z-10 bg-zinc-50">
                <tr
                  class="h-12 border-b border-zinc-200 bg-zinc-50 text-left text-[11px] font-bold uppercase text-zinc-600"
                >
                  <th class="px-5">Forma de pagamento</th>
                  <th class="w-32.5 px-4 text-center">Valor</th>
                  <th class="w-37.5 px-4 text-center">Parcelas</th>
                  <th class="w-35 px-4 text-center" />
                </tr>
              </thead>
              <tbody class="max-h-96 overflow-y-scroll divide-y divide-zinc-100">
                <template v-if="payments.length > 0">
                  <tr
                    v-for="(payment, index) in payments"
                    :key="index"
                    class="h-12 hover:bg-zinc-50/50 transition-colors text-zinc-700"
                  >
                    <td class="px-5 font-medium">
                      {{ getPaymentMethodName(payment.forma_pagamento_id) }}
                    </td>
                    <td class="px-4 text-center">{{ formatCurrency(payment.valor) }}</td>
                    <td class="px-4 text-center">
                      {{ payment.parcelado ? `${payment.qtd_parcelas}x` : '1x' }}
                    </td>
                    <td class="px-4 flex items-center justify-center h-12">
                      <button
                        type="button"
                        class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-500 shadow-sm transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                        @click.stop="handleRemovePayment(index)"
                      >
                        <Trash2 class="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                </template>

                <tr v-else>
                  <td colspan="4" class="px-6 py-5">
                    <div
                      class="mx-auto flex max-w-md flex-col items-center justify-center text-center"
                    >
                      <div
                        class="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-brand-primary"
                      >
                        <TicketX class="h-5 w-5" />
                      </div>

                      <h3 class="text-sm font-bold text-zinc-900">Nenhum pagamento adicionado</h3>

                      <p class="mt-2 text-xs leading-6 text-zinc-500">
                        Clique no botão "Adicionar pagamento" para registrar um pagamento para esta
                        venda.
                      </p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3">
        <BaseButton variant="secondary" size="md" @click="closeFinishModal">Cancelar</BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          :disabled="!canFinish || finishMutation.isPending.value"
          @click="handleFinish"
        >
          {{ finishMutation.isPending.value ? 'Finalizando...' : 'Finalizar Venda' }}
        </BaseButton>
      </div>
    </template>

    <AddPaymentModal
      :is-open="addPaymentModalIsOpen"
      :restante="restante"
      @close="closeAddPaymentModal"
      @add="handleAddPayment"
    />
  </BaseModal>
</template>
