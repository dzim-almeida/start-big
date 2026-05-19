<script setup lang="ts">
import { ref, computed } from 'vue';
import { X } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';

import { formatCurrency } from '@/shared/utils/finance';
import { inferPaymentType, inferPermiteParcelamento } from '@/modules/order-service/shared/utils/formatters';

import { usePaymentMethodsQuery } from '../../composables/queries/usePaymentMethodsQuery';

import type { PaymentSaleCreate } from '../../schemas/paymentSale.schema';

const props = defineProps<{
  isOpen: boolean;
  restante: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'add', payment: PaymentSaleCreate): void;
}>();

const { formasPagamento } = usePaymentMethodsQuery();

const selectedFormaPagamentoId = ref<number | undefined>(undefined);
const amount = ref<number>(0);
const parcelas = ref<number>(1);

const paymentOptions = computed(() =>
  formasPagamento.value
    .filter((fp) => fp.ativo)
    .map((fp) => ({ label: fp.nome, value: fp.id }))
);

const parcelasOptions = Array.from({ length: 12 }, (_, i) => ({
  label: `${i + 1}x`,
  value: i + 1,
}));

const selectedMethod = computed(() =>
  formasPagamento.value.find((fp) => fp.id === selectedFormaPagamentoId.value)
);

const displayParcelas = computed(() => {
  if (!selectedMethod.value) return false;
  const tipo = selectedMethod.value.tipo ?? inferPaymentType(selectedMethod.value.nome);
  return inferPermiteParcelamento(tipo);
});

const isParcelado = computed(() => displayParcelas.value && parcelas.value > 1);

const hasSelectedMethod = computed(() => !!selectedFormaPagamentoId.value);

const displayRestante = computed(() => formatCurrency(props.restante));

function resetForm() {
  selectedFormaPagamentoId.value = formasPagamento.value.length > 0 ? formasPagamento.value[0].id : undefined;
  amount.value = 0;
  parcelas.value = 1;
}

function handleClose() {
  resetForm();
  emit('close');
}

function handleAddPayment() {
  if (amount.value <= 0 || !selectedFormaPagamentoId.value) return;

  const valorCentavos = Math.round(amount.value * 100);

  const payment = {
    forma_pagamento_id: selectedFormaPagamentoId.value,
    parcelado: isParcelado.value,
    qtd_parcelas: isParcelado.value ? parcelas.value : null,
    valor: valorCentavos,
  } as PaymentSaleCreate;

  emit('add', payment);
  resetForm();
  emit('close');
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Adicionar Pagamento" size="md">
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-zinc-800">Novo Pagamento</h2>
        </div>

        <button
          type="button"
          class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          @click="handleClose"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <div class="p-6 flex flex-col gap-6 w-full">
      <div class="flex flex-col gap-2">
        <label class="text-sm font-semibold text-zinc-700">Forma de Pagamento</label>
        <BaseSelect
          v-model="selectedFormaPagamentoId"
          :options="paymentOptions"
          placeholder="Selecione o tipo"
          class="w-full z-999"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-semibold text-zinc-700">Valor (R$)</label>
        <MoneyInput v-model="amount" placeholder="0,00" class="w-full text-lg" :disabled="!hasSelectedMethod" />
      </div>

      <div v-if="displayParcelas" class="flex flex-col gap-2">
        <label class="text-sm font-semibold text-zinc-700">Parcelas</label>
        <BaseSelect
          v-model="parcelas"
          :options="parcelasOptions"
          placeholder="Selecione a quantidade"
          class="w-full z-999"
        />
      </div>

      <div>
        <h1 class="mb-2 font-poppins font-bold text-md text-zinc-800 uppercase tracking-wider">
          Restante a pagar
        </h1>
        <p class="font-bold text-3xl" :class="restante > 0 ? 'text-red-600' : 'text-green-600'">
          {{ displayRestante }}
        </p>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 border-zinc-200 bg-zinc-50 rounded-b-2xl">
        <BaseButton variant="secondary" size="md" @click="handleClose"> Cancelar </BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          @click="handleAddPayment"
          :disabled="amount <= 0 || !selectedFormaPagamentoId"
        >
          Confirmar Adição
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
