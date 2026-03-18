<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import {
  FileText,
  AlertTriangle,
  CreditCard,
  Wallet,
  QrCode,
  Banknote,
  CheckCircle2,
  Trash2,
} from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';

import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { PaymentFormReadDataType } from '@/shared/schemas/payments/payment.schema';
import { formatCurrency } from '@/shared/utils/finance';
import { useOSFinalizarForm } from '../composables/form/useOSFinalizar.form';
import { useOsPaymentMethodsGet } from '../composables/request/relationship/useOSPaymentMethods.queries';
import { inferPaymentType, inferPermiteParcelamento, getPaymentDisplayName } from '../../shared/utils/formatters';

interface Props {
  isOpen: boolean;
  osNumero: string | null;
  ordemServico: OrderServiceReadDataType | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  finalized: [payload: { shouldPrint: boolean }];
}>();

const shouldPrint = ref(false);
const confirmacao = ref(false);
const hasAttemptedSubmit = ref(false);

const showPaymentDetails = ref(false);
const currentPaymentMethod = ref<PaymentFormReadDataType | null>(null);
const paymentDetails = ref({ valor: 0, parcelas: 1, bandeira: '' });

const osNumberRef = computed(() => props.osNumero);

const finalizarForm = useOSFinalizarForm({
  osNumber: osNumberRef,
  onSuccess: () => {
    emit('finalized', { shouldPrint: shouldPrint.value });
    shouldPrint.value = false;
    confirmacao.value = false;
  },
});

const { formasPagamento } = useOsPaymentMethodsGet();

// Sincronizar desconto (form está em centavos)
const descontoDisplay = ref(0);
watch(descontoDisplay, (val) => {
  finalizarForm.desconto.value = Math.round(val * 100);
});

watch(() => props.isOpen, (open) => {
  if (!open) {
    hasAttemptedSubmit.value = false;
    finalizarForm.resetForm();
    descontoDisplay.value = 0;
    shouldPrint.value = false;
    confirmacao.value = false;
    showPaymentDetails.value = false;
    currentPaymentMethod.value = null;
  }
});

const subtotalItens = computed(() => {
  if (!props.ordemServico?.itens) return 0;
  return props.ordemServico.itens.reduce((sum, item) => sum + item.valor_total, 0);
});

const valorTotal = computed(() => {
  const desconto = finalizarForm.desconto.value ?? 0;
  return Math.max(0, subtotalItens.value - desconto);
});

const totalPago = computed(() =>
  finalizarForm.pagamentos.value.reduce((sum, p) => sum + (p.value.valor ?? 0), 0),
);

const restante = computed(() => Math.max(0, valorTotal.value - totalPago.value));
const troco = computed(() => Math.max(0, totalPago.value - valorTotal.value));

const canSubmit = computed(() =>
  confirmacao.value &&
  (finalizarForm.solucao.value?.trim().length ?? 0) >= 5 &&
  totalPago.value >= valorTotal.value,
);

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

function getPaymentMethodById(id: number): PaymentFormReadDataType | undefined {
  return formasPagamento.value.find((f) => f.id === id);
}

function getPaymentIconById(id: number) {
  const method = getPaymentMethodById(id);
  return getPaymentIcon(method ? getMethodTipo(method) : '');
}

const paymentValueReais = ref(0);

function handleAddPaymentClick(method: PaymentFormReadDataType) {
  currentPaymentMethod.value = method;
  paymentValueReais.value = restante.value / 100;
  paymentDetails.value = { valor: 0, parcelas: 1, bandeira: '' };
  showPaymentDetails.value = true;
}

function confirmAddPayment() {
  if (!currentPaymentMethod.value) return;
  finalizarForm.handleAddPagamento({
    forma_pagamento_id: currentPaymentMethod.value.id,
    valor: Math.round(paymentValueReais.value * 100),
    parcelas: paymentDetails.value.parcelas,
    bandeira_cartao: paymentDetails.value.bandeira || undefined,
  });
  showPaymentDetails.value = false;
  currentPaymentMethod.value = null;
}

function removePayment(index: number) {
  finalizarForm.handleRemovePagamento(index);
}

function handleSubmit() {
  hasAttemptedSubmit.value = true;
  finalizarForm.onSubmit();
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Finalizar Ordem de Serviço"
    :subtitle="osNumero ? `OS: ${osNumero}` : ''"
    size="xl"
    @close="emit('close')"
  >
    <div v-if="hasAttemptedSubmit && finalizarForm.errors.value.pagamentos" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-3">
      <AlertTriangle :size="20" class="shrink-0 mt-0.5" />
      <span>{{ finalizarForm.errors.value.pagamentos }}</span>
    </div>

    <form @submit.prevent="handleSubmit" class="flex flex-col lg:flex-row gap-8">
      <div class="flex-1 space-y-6">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <CheckCircle2 :size="18" class="text-emerald-600" />
            <label class="text-sm font-semibold text-zinc-700">Solução Aplicada <span class="text-red-500">*</span></label>
          </div>
          <BaseTextarea
            v-model="finalizarForm.solucao.value"
            placeholder="Descreva o serviço realizado..."
            :rows="4"
            :error="finalizarForm.errors.value.solucao"
          />
        </div>

        <div>
          <label class="text-sm font-semibold text-zinc-700">Observações</label>
          <BaseTextarea
            v-model="finalizarForm.observacoes.value"
            :rows="2"
            placeholder="Notas adicionais..."
            class="mt-2"
          />
        </div>
      </div>

      <div class="w-full lg:w-96 space-y-6">
        <div class="bg-zinc-50 rounded-2xl p-5 border border-zinc-200 shadow-sm">
          <div class="space-y-3">
            <div class="flex justify-between text-base">
              <span class="text-zinc-600">Subtotal</span>
              <span class="font-medium">{{ formatCurrency(subtotalItens) }}</span>
            </div>

            <div class="flex justify-between items-center text-sm">
              <span class="text-zinc-500">Desconto</span>
              <div class="w-32">
                <BaseMoneyInput v-model="descontoDisplay" label="" />
              </div>
            </div>

            <div class="flex justify-between items-center text-lg font-bold pt-2 border-t border-zinc-200">
              <span class="text-zinc-800">Total</span>
              <span class="text-emerald-600">{{ formatCurrency(valorTotal) }}</span>
            </div>

            <div v-if="restante > 0" class="flex justify-between items-center text-sm text-red-600 font-medium pt-1">
              <span>Faltam</span>
              <span>{{ formatCurrency(restante) }}</span>
            </div>
            <div v-if="troco > 0" class="flex justify-between items-center text-sm text-brand-primary font-medium pt-1">
              <span>Troco</span>
              <span>{{ formatCurrency(troco) }}</span>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-semibold text-zinc-700">Pagamentos</label>
            <span class="text-xs text-zinc-500">{{ finalizarForm.pagamentos.value.length }} item(s)</span>
          </div>

          <div v-if="finalizarForm.pagamentos.value.length === 0" class="text-center py-6 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-xs text-zinc-400">Nenhum pagamento registrado</p>
          </div>

          <div v-else class="space-y-2">
            <div v-for="(pgto, idx) in finalizarForm.pagamentos.value" :key="idx" class="flex items-center justify-between p-3 bg-white border border-zinc-100 rounded-xl shadow-sm">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-zinc-50 rounded-lg text-zinc-500">
                  <component :is="getPaymentIconById(pgto.value.forma_pagamento_id)" :size="16" />
                </div>
                <div>
                  <p class="text-sm font-medium text-zinc-700">{{ getPaymentDisplayName(getPaymentMethodById(pgto.value.forma_pagamento_id)?.nome ?? 'Pagamento') }}</p>
                  <p class="text-xs text-zinc-400">
                    {{ formatCurrency(pgto.value.valor) }}
                    <span v-if="pgto.value.parcelas > 1">em {{ pgto.value.parcelas }}x</span>
                  </p>
                </div>
              </div>
              <button type="button" @click="removePayment(idx)" class="text-zinc-400 hover:text-red-500 p-2">
                <Trash2 :size="16" />
              </button>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="method in formasPagamento"
            :key="method.id"
            type="button"
            class="flex flex-col items-center justify-center p-2 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50 hover:border-emerald-500 hover:text-emerald-600 transition-all gap-1 h-16 shadow-sm"
            :disabled="restante <= 0"
            @click="handleAddPaymentClick(method)"
          >
            <component :is="getPaymentIcon(getMethodTipo(method))" :size="20" />
            <span class="text-[10px] font-medium text-center leading-tight">{{ getPaymentDisplayName(method.nome) }}</span>
          </button>
        </div>

        <div class="p-2">
          <BaseCheckbox
            v-model="confirmacao"
            :label="`Confirmo a conclusão e recebimento (${formatCurrency(totalPago)})`"
          />
        </div>

        <BaseButton
          type="submit"
          variant="primary"
          :is-loading="finalizarForm.isPending.value"
          :disabled="!canSubmit"
          class="w-full py-3 shadow-lg shadow-blue-600/20"
        >
          Finalizar ({{ formatCurrency(valorTotal) }})
        </BaseButton>
      </div>
    </form>

    <!-- Dialog de detalhes do pagamento -->
    <div v-if="showPaymentDetails && currentPaymentMethod" class="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4 animate-in fade-in zoom-in duration-200">
        <div class="flex items-center gap-3 mb-4">
          <div class="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <component :is="getPaymentIcon(getMethodTipo(currentPaymentMethod))" :size="24" />
          </div>
          <div>
            <h3 class="font-bold text-lg text-zinc-800">{{ getPaymentDisplayName(currentPaymentMethod.nome) }}</h3>
            <p class="text-xs text-zinc-500">Detalhes do pagamento</p>
          </div>
        </div>

        <BaseMoneyInput
          v-model="paymentValueReais"
          label="Valor a Pagar"
        />

        <div v-if="getMethodPermiteParcelamento(currentPaymentMethod)">
          <BaseSelect
            v-model="paymentDetails.parcelas"
            label="Parcelamento"
            :options="[
              { value: 1, label: 'À vista' },
              { value: 2, label: '2x' },
              { value: 3, label: '3x' },
              { value: 4, label: '4x' },
              { value: 5, label: '5x' },
              { value: 6, label: '6x' },
              { value: 7, label: '7x' },
              { value: 8, label: '8x' },
              { value: 9, label: '9x' },
              { value: 10, label: '10x' },
              { value: 11, label: '11x' },
              { value: 12, label: '12x' },
            ]"
          />
        </div>

        <div v-if="getMethodTipo(currentPaymentMethod).includes('CARTAO')">
          <BaseSelect
            v-model="paymentDetails.bandeira"
            label="Bandeira"
            :options="[
              { value: '', label: 'Selecione...' },
              { value: 'VISA', label: 'Visa' },
              { value: 'MASTERCARD', label: 'Mastercard' },
              { value: 'ELO', label: 'Elo' },
              { value: 'OUTROS', label: 'Outros' },
            ]"
          />
        </div>

        <div v-if="getMethodTipo(currentPaymentMethod) === 'PIX'" class="text-center py-2">
          <div class="border-2 border-dashed border-emerald-500/30 bg-emerald-50 rounded-lg p-4 inline-block">
            <QrCode :size="48" class="text-emerald-700" />
          </div>
          <p class="text-[10px] text-zinc-500 mt-2">QR Code gerado para cobrança.</p>
        </div>

        <div class="pt-4 flex gap-3">
          <BaseButton variant="secondary" class="flex-1" @click="showPaymentDetails = false">Cancelar</BaseButton>
          <BaseButton variant="primary" class="flex-1" @click="confirmAddPayment">Confirmar</BaseButton>
        </div>
      </div>
    </div>

    <template #footer><span></span></template>
  </BaseModal>
</template>
