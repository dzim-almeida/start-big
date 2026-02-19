<script setup lang="ts">
import {
  FileText,
  AlertTriangle,
  CreditCard,
  Wallet,
  QrCode,
  Banknote,
  CheckCircle2,
  ShieldCheck,
  Trash2,
  MessageSquare,
} from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';

import type { OrdemServicoRead } from '../types/ordemServico.types';
import { formatCurrency } from '@/shared/utils/finance';
import { useOSFinalization } from '../composables/useOSFinalization';

interface Props {
  isOpen: boolean;
  ordemServico: OrdemServicoRead | null;
  valorTotal?: number;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  finalized: [payload: { os: OrdemServicoRead; shouldPrint: boolean }];
}>();

const {
  form,
  errors,
  confirmacao,
  apiError,
  formasPagamento,
  addedPayments,
  currentPaymentMethod,
  paymentDetails,
  showPaymentDetails,
  subtotalItens,
  valorTotalDisplay,
  totalPago,
  restante,
  troco,
  canSubmit,
  isPending,
  handleAddPaymentClick,
  confirmAddPayment,
  removePayment,
  handleDescontoInput,
  handleClose,
  handleSubmit,
} = useOSFinalization(props, emit);

function getPaymentIcon(type: string) {
  switch (type) {
    case 'DINHEIRO': return Banknote;
    case 'PIX': return QrCode;
    case 'CARTAO_CREDITO': return CreditCard;
    case 'CARTAO_DEBITO': return Wallet;
    case 'BOLETO': return FileText;
    default: return Banknote;
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Finalizar Ordem de Serviço"
    :subtitle="ordemServico ? `OS: ${ordemServico.numero}` : ''"
    size="xl"
    @close="handleClose"
  >
    <div v-if="apiError" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-3">
      <AlertTriangle :size="20" class="shrink-0 mt-0.5" />
      <span>{{ apiError }}</span>
    </div>

    <form @submit.prevent="handleSubmit" class="flex flex-col lg:flex-row gap-8">
      <div class="flex-1 space-y-6">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <CheckCircle2 :size="18" class="text-emerald-600" />
            <label class="text-sm font-semibold text-zinc-700">Solução Aplicada <span class="text-red-500">*</span></label>
          </div>
          <BaseTextarea
            v-model="form.solucao"
            placeholder="Descreva o serviço realizado..."
            :rows="4"
            :error="errors.solucao"
          />
        </div>

        <div>
          <div class="flex items-center gap-2 mb-2">
            <ShieldCheck :size="18" class="text-zinc-500" />
            <label class="text-sm font-semibold text-zinc-700">Garantia</label>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex gap-2">
              <button v-for="days in [30, 90, 180]" :key="days" type="button"
                class="px-4 py-2 text-xs font-medium rounded-full border transition-all"
                :class="form.garantia_dias === days ? 'bg-emerald-100 border-emerald-300 text-emerald-700' : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50'"
                @click="form.garantia_dias = days"
              >
                {{ days }}d
              </button>
            </div>
            <div class="w-24">
              <BaseInput v-model.number="form.garantia_dias" type="number" />
            </div>
          </div>
        </div>

        <div>
          <div class="flex items-center gap-2 mb-2">
            <MessageSquare :size="18" class="text-zinc-500" />
            <label class="text-sm font-semibold text-zinc-700">Observações</label>
          </div>
          <BaseTextarea
            v-model="form.observacoes"
            :rows="2"
            placeholder="Notas adicionais..."
          />
        </div>
      </div>

      <div class="w-full lg:w-96 space-y-6">
        <div class="bg-zinc-50 rounded-2xl p-5 border border-zinc-200 shadow-sm relative overflow-hidden">
          <div class="space-y-3">
            <div class="flex justify-between text-base">
              <span class="text-zinc-600">Subtotal</span>
              <span class="font-medium">{{ formatCurrency(subtotalItens) }}</span>
            </div>

            <div class="flex justify-between items-center text-sm">
              <span class="text-zinc-500">Desconto</span>
              <div class="w-28">
                <BaseInput v-model="form.desconto" @input="handleDescontoInput" />
              </div>
            </div>

            <div class="flex justify-between items-center text-lg font-bold pt-2 border-t border-zinc-200">
              <span class="text-zinc-800">Total</span>
              <span class="text-emerald-600">{{ valorTotalDisplay }}</span>
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
            <span class="text-xs text-zinc-500">{{ addedPayments.length }} item(s)</span>
          </div>

          <div v-if="addedPayments.length === 0" class="text-center py-6 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-xs text-zinc-400">Nenhum pagamento registrado</p>
          </div>

          <div v-else class="space-y-2">
            <div v-for="(pgto, idx) in addedPayments" :key="idx" class="flex items-center justify-between p-3 bg-white border border-zinc-100 rounded-xl shadow-sm">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-zinc-50 rounded-lg text-zinc-500">
                  <component :is="getPaymentIcon(pgto.detalhes?.tipo || 'DINHEIRO')" :size="16" />
                </div>
                <div>
                  <p class="text-sm font-medium text-zinc-700">{{ pgto.detalhes?.nome }}</p>
                  <p class="text-xs text-zinc-400">
                    {{ formatCurrency(pgto.valor) }}
                    <span v-if="pgto.parcelas > 1">em {{ pgto.parcelas }}x</span>
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
            <component :is="getPaymentIcon(method.tipo)" :size="20" />
            <span class="text-[10px] font-medium text-center leading-tight">{{ method.nome }}</span>
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
          :is-loading="isPending"
          :disabled="!canSubmit"
          class="w-full py-3 shadow-lg shadow-blue-600/20"
        >
          Finalizar ({{ valorTotalDisplay }})
        </BaseButton>
      </div>
    </form>

    <div v-if="showPaymentDetails && currentPaymentMethod" class="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4 animate-in fade-in zoom-in duration-200">
        <div class="flex items-center gap-3 mb-4">
          <div class="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <component :is="getPaymentIcon(currentPaymentMethod.tipo)" :size="24" />
          </div>
          <div>
            <h3 class="font-bold text-lg text-zinc-800">{{ currentPaymentMethod.nome }}</h3>
            <p class="text-xs text-zinc-500">Detalhes do pagamento</p>
          </div>
        </div>

        <div>
          <label class="text-xs font-semibold text-zinc-500">Valor a Pagar</label>
          <div class="relative mt-1">
            <span class="absolute left-3 top-2.5 text-zinc-400">R$</span>
            <input v-model="paymentDetails.valor" class="w-full pl-10 pr-4 py-2 border border-zinc-300 rounded-xl text-lg font-bold text-zinc-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none" />
          </div>
        </div>

        <div v-if="currentPaymentMethod.permite_parcelamento">
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

        <div v-if="currentPaymentMethod.tipo.includes('CARTAO')">
          <BaseSelect
            v-model="paymentDetails.bandeira"
            label="Bandeira"
            :options="[
              { value: '', label: 'Selecione...' },
              { value: 'VISA', label: 'Visa' },
              { value: 'MASTERCARD', label: 'Mastercard' },
              { value: 'ELO', label: 'Elo' },
              { value: 'AMEX', label: 'Amex' },
            ]"
          />
        </div>

        <div v-if="currentPaymentMethod.tipo === 'PIX'" class="text-center py-2">
          <div class="border-2 border-dashed border-emerald-500/30 bg-emerald-50 rounded-lg p-4 inline-block">
            <QrCode :size="48" class="text-emerald-700" />
          </div>
          <p class="text-[10px] text-zinc-500 mt-2">QR Code gerado para cobrança.</p>
        </div>

        <div class="pt-4 flex gap-3">
          <BaseButton variant="secondary" class="flex-1" @click="showPaymentDetails = false">Cancelar</BaseButton>
          <BaseButton variant="success" class="flex-1" @click="confirmAddPayment">Confirmar</BaseButton>
        </div>
      </div>
    </div>

    <template #footer><span></span></template>
  </BaseModal>
</template>
