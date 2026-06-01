<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  X,
  CheckCircle,
  Trash2,
  CreditCard,
  Wallet,
  QrCode,
  Banknote,
  FileText,
  Info,
} from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';
import {
  getPaymentDisplayName,
  inferPaymentType,
  inferPermiteParcelamento,
} from '@/shared/utils/print.utils';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';

import { useFinishSaleModal } from '../../composables/flows/useFinishSaleModal';
import { useFinishSaleMutation } from '../../composables/mutates/useFinishSaleMutation';
import { usePaymentMethodsQuery } from '../../composables/queries/usePaymentMethodsQuery';
import { useSaleModal } from '../../composables/flows/useSaleModal';

import type { SaleRead } from '../../schemas/sale.schema';
import type { PaymentFormReadDataType } from '@/shared/schemas/payments/payment.schema';

const props = defineProps<{
  sale: SaleRead | undefined;
}>();

const emit = defineEmits<{
  finalized: [sale: SaleRead];
}>();

const saleTotal = computed(() => props.sale?.total ?? 0);

const {
  payments,
  finishModalIsOpen,
  closeFinishModal,
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

// Estado local do modal aninhado de pagamento
const showPaymentDetails = ref(false);
const currentPaymentMethod = ref<PaymentFormReadDataType | null>(null);
const paymentValueReais = ref(0);
const paymentParcelas = ref(1);
const confirmacao = ref(false);

// Computed values
const activePaymentMethods = computed(() =>
  formasPagamento.value.filter((fp) => fp.ativo),
);

const displaySubtotal = computed(() => formatCurrency(props.sale?.subtotal ?? 0));
const displayDiscount = computed(() => formatCurrency(props.sale?.descontos ?? 0));
const displayDelivery = computed(() => formatCurrency(props.sale?.entrega ?? 0));
const displayTotal = computed(() => formatCurrency(props.sale?.total ?? 0));
const displayTotalPago = computed(() => formatCurrency(totalPago.value));
const displayTroco = computed(() => formatCurrency(troco.value));
const displayRestante = computed(() => formatCurrency(restante.value));

const canFinishWithConfirmation = computed(() => canFinish.value && confirmacao.value);

const parcelasOptions = Array.from({ length: 12 }, (_, i) => ({
  label: i === 0 ? 'À vista' : `${i + 1}x`,
  value: i + 1,
}));

// Helpers de pagamento
function getMethodTipo(method: PaymentFormReadDataType): string {
  return method.tipo ?? inferPaymentType(method.nome);
}

function getMethodPermiteParcelamento(method: PaymentFormReadDataType): boolean {
  return method.permite_parcelamento ?? inferPermiteParcelamento(getMethodTipo(method));
}

function getPaymentIcon(tipo: string) {
  switch (tipo) {
    case 'DINHEIRO': return Banknote;
    case 'PIX': return QrCode;
    case 'CARTAO_CREDITO': return CreditCard;
    case 'CARTAO_DEBITO': return Wallet;
    case 'BOLETO': return FileText;
    default: return Banknote;
  }
}

function getPaymentIconById(id: number) {
  const method = formasPagamento.value.find((f) => f.id === id);
  return getPaymentIcon(method ? getMethodTipo(method) : '');
}

function getPaymentMethodName(formaId: number): string {
  const method = formasPagamento.value.find((fp) => fp.id === formaId);
  return getPaymentDisplayName(method?.nome ?? 'Desconhecido');
}

// Ações de pagamento
function handleAddPaymentClick(method: PaymentFormReadDataType) {
  currentPaymentMethod.value = method;
  paymentValueReais.value = restante.value / 100;
  paymentParcelas.value = 1;
  showPaymentDetails.value = true;
}

function confirmAddPayment() {
  if (!currentPaymentMethod.value || paymentValueReais.value <= 0) return;

  const valorCentavos = Math.round(paymentValueReais.value * 100);
  const parcelado = getMethodPermiteParcelamento(currentPaymentMethod.value) && paymentParcelas.value > 1;

  addPayment({
    forma_pagamento_id: currentPaymentMethod.value.id,
    parcelado,
    qtd_parcelas: parcelado ? paymentParcelas.value : null,
    valor: valorCentavos,
  });

  showPaymentDetails.value = false;
  currentPaymentMethod.value = null;
}

function handleRemovePayment(index: number) {
  removePayment(index);
}

function handleCloseFinishModal() {
  confirmacao.value = false;
  closeFinishModal();
}

function handleFinish() {
  if (!props.sale || !canFinishWithConfirmation.value) return;

  finishMutation.mutate(
    { saleId: props.sale.id, payments: payments.value },
    {
      onSuccess: (finishedSale) => {
        confirmacao.value = false;
        closeFinishModal();
        emit('finalized', finishedSale);
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
          @click="handleCloseFinishModal"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <div class="w-full flex flex-col gap-4">
      <!-- Info Banner -->
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

      <!-- Conteúdo principal: 2 colunas -->
      <div class="w-full border border-zinc-200 rounded-xl flex">
        <!-- COLUNA ESQUERDA: Resumo Financeiro -->
        <div class="p-5 w-1/2 flex flex-col gap-2 border-r border-zinc-200">
          <h3 class="mb-2 font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
            Resumo Financeiro
          </h3>
          <div class="flex justify-between items-center">
            <span class="font-medium text-sm text-zinc-600">Subtotal dos itens</span>
            <span class="font-bold text-sm text-zinc-600">{{ displaySubtotal }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="font-medium text-sm text-zinc-600">Desconto</span>
            <span class="font-bold text-sm text-red-600">- {{ displayDiscount }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="font-medium text-sm text-zinc-600">Entrega</span>
            <span class="font-bold text-sm text-green-600">+ {{ displayDelivery }}</span>
          </div>

          <div class="mt-auto pt-5 flex items-start justify-between border-t border-zinc-200">
            <span class="font-bold text-lg text-zinc-700">Total da Venda</span>
            <span class="font-bold text-2xl text-zinc-700">{{ displayTotal }}</span>
          </div>
        </div>

        <!-- COLUNA DIREITA: Pagamentos -->
        <div class="p-5 flex-1 flex flex-col gap-4">
          <!-- Header pagamentos -->
          <div class="flex items-center justify-between">
            <h3 class="font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
              Pagamentos
            </h3>
            <span class="text-xs text-zinc-500">{{ payments.length }} item(s)</span>
          </div>

          <!-- Lista de pagamentos como cards -->
          <div v-if="payments.length === 0" class="text-center py-5 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-xs text-zinc-400">Nenhum pagamento registrado</p>
          </div>

          <div v-else class="space-y-2 max-h-40 overflow-y-auto">
            <div
              v-for="(payment, idx) in payments"
              :key="idx"
              class="flex items-center justify-between p-3 bg-white border border-zinc-100 rounded-xl shadow-sm"
            >
              <div class="flex items-center gap-3">
                <div class="p-2 bg-zinc-50 rounded-lg text-brand-primary">
                  <component :is="getPaymentIconById(payment.forma_pagamento_id)" :size="16" />
                </div>
                <div>
                  <p class="text-sm font-medium text-zinc-700">
                    {{ getPaymentMethodName(payment.forma_pagamento_id) }}
                  </p>
                  <p class="text-xs text-zinc-400">
                    {{ formatCurrency(payment.valor) }}
                    <span v-if="payment.parcelado"> em {{ payment.qtd_parcelas }}x</span>
                  </p>
                </div>
              </div>
              <button
                type="button"
                class="text-zinc-400 hover:text-red-500 p-2 cursor-pointer"
                @click="handleRemovePayment(idx)"
              >
                <Trash2 :size="16" />
              </button>
            </div>
          </div>

          <!-- Grid de formas de pagamento -->
          <div data-payment-grid class="grid grid-cols-3 gap-2">
            <button
              v-for="method in activePaymentMethods"
              :key="method.id"
              type="button"
              class="flex flex-col items-center justify-center p-2 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50 hover:border-brand-primary hover:text-brand-primary transition-all gap-1 h-16 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="restante <= 0"
              @click="handleAddPaymentClick(method)"
            >
              <component :is="getPaymentIcon(getMethodTipo(method))" :size="20" />
              <span class="text-[10px] font-medium text-center leading-tight">
                {{ getPaymentDisplayName(method.nome) }}
              </span>
            </button>
          </div>

          <!-- Restante / Troco -->
          <div class="pt-3 border-t border-zinc-200 space-y-2">
            <div v-if="restante > 0" class="flex justify-between items-center text-sm text-red-600 font-medium">
              <span>Faltam</span>
              <span>{{ displayRestante }}</span>
            </div>
            <div v-if="troco > 0" class="flex justify-between items-center text-sm text-amber-600 font-medium">
              <span>Troco</span>
              <span>{{ displayTroco }}</span>
            </div>
          </div>

          <!-- Total Pago card -->
          <div class="p-4 w-full bg-green-200 border border-green-500 rounded-xl">
            <h4 class="mb-1 font-poppins font-bold text-md text-green-700 uppercase tracking-wider">
              <CheckCircle :size="20" class="inline-block mr-2 text-green-700" /> Total Pago
            </h4>
            <p class="font-bold text-3xl text-green-700">{{ displayTotalPago }}</p>
          </div>

          <!-- Checkbox de confirmação -->
          <div class="pt-2">
            <BaseCheckbox
              v-model="confirmacao"
              :label="`Confirmo o recebimento de ${displayTotalPago}`"
            />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3">
        <BaseButton variant="secondary" size="md" @click="handleCloseFinishModal">Cancelar</BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          :disabled="!canFinishWithConfirmation || finishMutation.isPending.value"
          @click="handleFinish"
        >
          {{ finishMutation.isPending.value ? 'Finalizando...' : 'Finalizar Venda' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>

  <!-- Modal aninhado: Detalhes do pagamento -->
  <BaseModal
    :is-open="showPaymentDetails && !!currentPaymentMethod"
    :title="currentPaymentMethod ? getPaymentDisplayName(currentPaymentMethod.nome) : ''"
    subtitle="Detalhes do pagamento"
    size="sm"
    @close="showPaymentDetails = false"
  >
    <div v-if="currentPaymentMethod" class="space-y-4">
      <div class="flex items-center gap-3 pb-3 border-b border-zinc-100">
        <div class="p-3 bg-brand-secondary/20 text-brand-primary rounded-xl">
          <component :is="getPaymentIcon(getMethodTipo(currentPaymentMethod))" :size="24" />
        </div>
        <div>
          <p class="font-bold text-lg text-zinc-800">
            {{ getPaymentDisplayName(currentPaymentMethod.nome) }}
          </p>
          <p class="text-xs text-zinc-500">Restante: {{ displayRestante }}</p>
        </div>
      </div>

      <BaseMoneyInput
        v-model="paymentValueReais"
        label="Valor a Pagar"
      />

      <div v-if="getMethodPermiteParcelamento(currentPaymentMethod)">
        <BaseSelect
          v-model="paymentParcelas"
          label="Parcelamento"
          :options="parcelasOptions"
        />
      </div>

      <div class="pt-4 flex gap-3">
        <BaseButton variant="secondary" class="flex-1" @click="showPaymentDetails = false">
          Cancelar
        </BaseButton>
        <BaseButton
          variant="primary"
          class="flex-1"
          :disabled="paymentValueReais <= 0"
          @click="confirmAddPayment"
        >
          Confirmar
        </BaseButton>
      </div>
    </div>

    <template #footer><span></span></template>
  </BaseModal>
</template>
