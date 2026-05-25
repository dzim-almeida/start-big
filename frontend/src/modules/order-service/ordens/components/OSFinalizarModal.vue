<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import {
  FileText,
  AlertTriangle,
  CreditCard,
  Wallet,
  QrCode,
  Banknote,
  CheckCircle2,
  Trash2,
  Package,
  Percent,
  Tag,
  Truck,
  Wrench,
  ShoppingBag,
} from 'lucide-vue-next';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
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
import type { OsCardsFlagEnumDataType } from '../schemas/enums/osEnums.schema';

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

// ─── Estado local ──────────────────────────────────────────────────────────
const shouldPrint = ref(false);
const confirmacao = ref(false);
const hasAttemptedSubmit = ref(false);

const showPaymentDetails = ref(false);
const currentPaymentMethod = ref<PaymentFormReadDataType | null>(null);
const paymentDetails = ref<{ valor: number; parcelas: number; bandeira: OsCardsFlagEnumDataType | ''; taxa_juros: number }>({ valor: 0, parcelas: 1, bandeira: '', taxa_juros: 0 });

const osNumberRef = computed(() => props.osNumero);

// ─── Form composable ──────────────────────────────────────────────────────
const finalizarForm = useOSFinalizarForm({
  osNumber: osNumberRef,
  onSuccess: () => {
    emit('finalized', { shouldPrint: shouldPrint.value });
    shouldPrint.value = false;
    confirmacao.value = false;
  },
});

const { formasPagamento } = useOsPaymentMethodsGet();

// ─── Display values (reais) sincronizados com form (centavos) ──────────────
const descontoDisplay = ref(0);
watch(descontoDisplay, (val) => {
  const maxCents = Math.max(0, valorTotal.value - (finalizarForm.valor_entrada.value ?? 0));
  const maxReais = Math.round(maxCents) / 100;
  const clamped = Math.round(Math.max(0, Math.min(val, maxReais)) * 100) / 100;
  finalizarForm.desconto.value = Math.round(clamped * 100);
  if (val !== clamped) nextTick(() => { descontoDisplay.value = clamped; });
});

const taxaEntregaDisplay = ref(0);
watch(taxaEntregaDisplay, (val) => {
  finalizarForm.taxa_entrega.value = Math.round(val * 100);
});

const valorEntradaDisplay = ref(0);
watch(valorEntradaDisplay, (val) => {
  const maxCents = Math.max(0, valorTotal.value - (finalizarForm.desconto.value ?? 0));
  const maxReais = Math.round(maxCents) / 100;
  const clamped = Math.round(Math.max(0, Math.min(val, maxReais)) * 100) / 100;
  finalizarForm.valor_entrada.value = Math.round(clamped * 100);
  if (val !== clamped) nextTick(() => { valorEntradaDisplay.value = clamped; });
});

// ─── Cálculos financeiros ─────────────────────────────────────────────────
const subtotalItens = computed(() => {
  if (!props.ordemServico?.itens) return 0;
  return props.ordemServico.itens.reduce((sum, item) => sum + item.valor_total, 0);
});

// ─── Juros por pagamento (centavos, paralelo ao array de pagamentos) ─────────
const pagamentosJuros = ref<number[]>([]);

const acrescimoTotal = computed(() =>
  pagamentosJuros.value.reduce((sum, v) => sum + v, 0),
);

watch(acrescimoTotal, (val) => {
  finalizarForm.acrescimo.value = val;
}, { immediate: true });

watch(() => paymentDetails.value.taxa_juros, (v) => {
  const clamped = Math.min(100, Math.max(0, v ?? 0));
  if (v !== clamped) paymentDetails.value.taxa_juros = clamped;
});

// ─── Reset ao fechar / populate ao abrir ──────────────────────────────────
watch(() => props.isOpen, (open) => {
  if (open) {
    valorEntradaDisplay.value = (props.ordemServico?.valor_entrada ?? 0) / 100;
  } else {
    hasAttemptedSubmit.value = false;
    finalizarForm.resetForm();
    descontoDisplay.value = 0;
    taxaEntregaDisplay.value = 0;
    valorEntradaDisplay.value = 0;
    pagamentosJuros.value = [];
    shouldPrint.value = false;
    confirmacao.value = false;
    showPaymentDetails.value = false;
    currentPaymentMethod.value = null;
  }
});

const valorTotal = computed(() => {
  const entrega = finalizarForm.taxa_entrega.value ?? 0;
  const acresc = finalizarForm.acrescimo.value ?? 0;
  return Math.max(0, subtotalItens.value + entrega + acresc);
});

const valorEntrada = computed(() => finalizarForm.valor_entrada.value ?? 0);

const valorDesconto = computed(() => finalizarForm.desconto.value ?? 0);

const valorAdiantamento = computed(() => finalizarForm.valor_entrada.value ?? 0);

const totalPago = computed(() =>
  finalizarForm.pagamentos.value.reduce((sum, p) => sum + (p.value.valor ?? 0), 0),
);

// Valor líquido a cobrar via pagamentos (após descontos antecipados)
const totalAReceber = computed(() =>
  Math.max(0, valorTotal.value - valorAdiantamento.value - valorDesconto.value)
);

const restante = computed(() => Math.max(0, totalAReceber.value - totalPago.value));
const troco = computed(() => Math.max(0, totalPago.value - totalAReceber.value));

const canSubmit = computed(() =>
  confirmacao.value &&
  restante.value === 0,
);

// ─── Helpers de pagamento ─────────────────────────────────────────────────
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

// ─── Ações de pagamento ───────────────────────────────────────────────────
const paymentValueReais = ref(0);

function handleAddPaymentClick(method: PaymentFormReadDataType) {
  currentPaymentMethod.value = method;
  paymentValueReais.value = restante.value / 100;
  paymentDetails.value = { valor: 0, parcelas: 1, bandeira: '', taxa_juros: 0 };
  showPaymentDetails.value = true;
}

function confirmAddPayment() {
  if (!currentPaymentMethod.value) return;
  const baseValor = Math.round(paymentValueReais.value * 100);
  const jurosAmount = Math.round(baseValor * (paymentDetails.value.taxa_juros / 100));
  const totalValor = baseValor + jurosAmount;

  finalizarForm.handleAddPagamento({
    forma_pagamento_id: currentPaymentMethod.value.id,
    valor: totalValor,
    parcelas: paymentDetails.value.parcelas,
    bandeira_cartao: paymentDetails.value.bandeira || undefined,
  });
  pagamentosJuros.value = [...pagamentosJuros.value, jurosAmount];
  showPaymentDetails.value = false;
  currentPaymentMethod.value = null;
}

function removePayment(index: number) {
  finalizarForm.handleRemovePagamento(index);
  pagamentosJuros.value = pagamentosJuros.value.filter((_, i) => i !== index);
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
    size="2xl"
    @close="emit('close')"
  >
    <!-- Alerta de erro de pagamentos -->
    <div v-if="hasAttemptedSubmit && finalizarForm.errors.value.pagamentos" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-3">
      <AlertTriangle :size="20" class="shrink-0 mt-0.5" />
      <span>{{ finalizarForm.errors.value.pagamentos }}</span>
    </div>

    <form @submit.prevent="handleSubmit" class="flex flex-col lg:flex-row gap-8">

      <!-- ═══════════ COLUNA ESQUERDA ═══════════ -->
      <div class="flex-1 space-y-6 min-w-0">

        <!-- Tabela de itens unificada -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <Package :size="18" class="text-brand-primary" />
            <h3 class="text-sm font-semibold text-zinc-700">Itens da OS</h3>
            <span class="text-xs text-zinc-400">({{ ordemServico?.itens.length ?? 0 }})</span>
          </div>

          <div v-if="ordemServico?.itens && ordemServico.itens.length > 0" class="border border-zinc-200 rounded-xl overflow-hidden">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-zinc-100">
                  <th class="text-left px-3 py-2 text-xs font-medium uppercase tracking-wide text-zinc-400">Item</th>
                  <th class="text-center px-3 py-2 text-xs font-medium uppercase tracking-wide text-zinc-400 w-12">Qtd</th>
                  <th class="text-right px-3 py-2 text-xs font-medium uppercase tracking-wide text-zinc-400 w-24">Unitário</th>
                  <th class="text-right px-3 py-2 text-xs font-medium uppercase tracking-wide text-zinc-400 w-24">Total</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-100">
                <tr v-for="item in ordemServico.itens" :key="item.id" class="hover:bg-zinc-50/40 transition-colors">
                  <td class="px-3 py-2.5">
                    <div class="flex items-center gap-2">
                      <component
                        :is="item.tipo === 'SERVICO' ? Wrench : ShoppingBag"
                        :size="13"
                        class="shrink-0 text-brand-primary opacity-70"
                      />
                      <span class="text-zinc-700 truncate">{{ item.nome }}</span>
                    </div>
                  </td>
                  <td class="px-3 py-2.5 text-center text-zinc-500">{{ item.quantidade }}</td>
                  <td class="px-3 py-2.5 text-right text-zinc-500">{{ formatCurrency(item.valor_unitario) }}</td>
                  <td class="px-3 py-2.5 text-right font-medium text-zinc-700">{{ formatCurrency(item.valor_total) }}</td>
                </tr>
              </tbody>
              <tfoot class="bg-zinc-50 border-t border-zinc-200">
                <tr>
                  <td colspan="3" class="px-3 py-2 text-right text-xs font-semibold text-zinc-500 uppercase tracking-wide">Subtotal</td>
                  <td class="px-3 py-2 text-right text-sm font-bold text-zinc-800">{{ formatCurrency(subtotalItens) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div v-else class="text-center py-6 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-sm text-zinc-400">Nenhum item na OS</p>
          </div>
        </div>

        <!-- Solução Aplicada -->
        <div>
          <div class="flex items-center gap-2 mb-2">
            <CheckCircle2 :size="18" class="text-brand-primary" />
            <label class="text-sm font-semibold text-zinc-700">Solução Aplicada</label>
          </div>
          <BaseTextarea
            v-model="finalizarForm.solucao.value"
            placeholder="Descreva o serviço realizado, peças substituídas, testes efetuados..."
            :rows="4"
          />
        </div>

        <!-- Observações -->
        <div>
          <label class="text-sm font-semibold text-zinc-700">Observações</label>
          <BaseTextarea
            v-model="finalizarForm.observacoes.value"
            :rows="4"
            placeholder="Notas adicionais, condições de garantia, orientações ao cliente..."
            class="mt-2"
          />
        </div>
      </div>

      <!-- ═══════════ COLUNA DIREITA ═══════════ -->
      <div class="w-full lg:w-96 space-y-6 shrink-0">

        <!-- Resumo Financeiro -->
        <div class="bg-zinc-50 rounded-2xl p-5 border border-zinc-200 shadow-sm space-y-3">
          <h3 class="text-sm font-semibold text-zinc-700 mb-1">Resumo Financeiro</h3>

          <!-- Subtotal -->
          <div class="flex justify-between text-base">
            <span class="text-zinc-600">Subtotal</span>
            <span class="font-medium">{{ formatCurrency(subtotalItens) }}</span>
          </div>

          <!-- Taxa de Entrega -->
          <div class="flex justify-between items-center text-sm">
            <span class="text-zinc-500 flex items-center gap-1.5">
              <Truck :size="14" />
              Entrega
            </span>
            <div class="w-32">
              <BaseMoneyInput v-model="taxaEntregaDisplay" label="" />
            </div>
          </div>

          <!-- Desconto -->
          <div class="flex justify-between items-center text-sm">
            <span class="text-zinc-500 flex items-center gap-1.5">
              <Tag :size="14" />
              Desconto
            </span>
            <div class="w-32">
              <BaseMoneyInput v-model="descontoDisplay" label="" />
            </div>
          </div>

          <!-- Adiantamento -->
          <div class="flex justify-between items-center text-sm">
            <span class="text-emerald-600 flex items-center gap-1.5">
              <Banknote :size="14" />
              Adiantamento
            </span>
            <div class="w-32">
              <BaseMoneyInput v-model="valorEntradaDisplay" label="" />
            </div>
          </div>

          <!-- Juros / Acréscimo (read-only, reflexo dos juros por pagamento) -->
          <div v-if="(finalizarForm.acrescimo.value ?? 0) > 0" class="flex justify-between items-center text-sm">
            <span class="text-amber-600 flex items-center gap-1.5">
              <Percent :size="14" />
              Juros / Acréscimo
            </span>
            <span class="font-medium text-amber-600">+ {{ formatCurrency(finalizarForm.acrescimo.value ?? 0) }}</span>
          </div>

          <!-- Divisor -->
          <div class="border-t border-zinc-300 pt-3">
            <!-- Total -->
            <div class="flex justify-between items-center text-lg font-bold">
              <span class="text-zinc-800">Total</span>
              <span class="text-brand-primary">{{ formatCurrency(valorTotal) }}</span>
            </div>

            <!-- Desconto -->
            <div v-if="valorDesconto > 0" class="flex justify-between items-center text-sm font-bold mt-2">
              <span class="text-zinc-700">Desconto</span>
              <span class="text-zinc-800">- {{ formatCurrency(valorDesconto) }}</span>
            </div>

            <!-- Adiantamento -->
            <div v-if="valorEntrada > 0" class="flex justify-between items-center text-sm font-bold mt-2">
              <span class="text-zinc-700">Adiantamento</span>
              <span class="text-zinc-800">- {{ formatCurrency(valorAdiantamento) }}</span>
            </div>

            <!-- Restante / Troco -->
            <div v-if="restante > 0" class="flex justify-between items-center text-sm text-red-600 font-medium mt-2">
              <span>Faltam</span>
              <span>{{ formatCurrency(restante) }}</span>
            </div>
            <div v-if="troco > 0" class="flex justify-between items-center text-sm text-brand-primary font-medium mt-2">
              <span>Troco</span>
              <span>{{ formatCurrency(troco) }}</span>
            </div>
          </div>
        </div>

        <!-- Lista de Pagamentos -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-semibold text-zinc-700">Pagamentos</label>
            <span class="text-xs text-zinc-500">{{ finalizarForm.pagamentos.value.length }} item(s)</span>
          </div>

          <!-- Adiantamento como pagamento já efetuado -->
          <div
            v-if="valorEntrada > 0"
            class="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-100 rounded-xl"
          >
            <div class="flex items-center gap-3">
              <div class="p-2 bg-emerald-100 rounded-lg text-emerald-600">
                <CheckCircle2 :size="16" />
              </div>
              <div>
                <p class="text-sm font-medium text-emerald-700">Adiantamento</p>
                <p class="text-xs text-emerald-500">Pago anteriormente</p>
              </div>
            </div>
            <span class="text-sm font-bold text-emerald-700">{{ formatCurrency(valorEntrada) }}</span>
          </div>

          <div v-if="finalizarForm.pagamentos.value.length === 0" class="text-center py-5 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-xs text-zinc-400">Nenhum pagamento registrado</p>
          </div>

          <div v-else class="space-y-2 max-h-40 overflow-y-auto">
            <div v-for="(pgto, idx) in finalizarForm.pagamentos.value" :key="idx" class="flex items-center justify-between p-3 bg-white border border-zinc-100 rounded-xl shadow-sm">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-zinc-50 rounded-lg text-brand-primary">
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
              <button type="button" @click="removePayment(idx)" class="text-zinc-400 hover:text-red-500 p-2 cursor-pointer">
                <Trash2 :size="16" />
              </button>
            </div>
          </div>
        </div>

        <!-- Grid de Formas de Pagamento -->
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="method in formasPagamento"
            :key="method.id"
            type="button"
            class="flex flex-col items-center justify-center p-2 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50 hover:border-brand-primary hover:text-brand-primary transition-all gap-1 h-16 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="restante <= 0"
            @click="handleAddPaymentClick(method)"
          >
            <component :is="getPaymentIcon(getMethodTipo(method))" :size="20" />
            <span class="text-[10px] font-medium text-center leading-tight">{{ getPaymentDisplayName(method.nome) }}</span>
          </button>
        </div>

        <!-- Confirmação + Submit -->
        <div class="space-y-3 pt-2 border-t border-zinc-200">
          <BaseCheckbox
            v-model="confirmacao"
            :label="`Confirmo a conclusão e recebimento (${formatCurrency(totalPago)})`"
          />

          <BaseButton
            type="submit"
            variant="primary"
            :is-loading="finalizarForm.isPending.value"
            :disabled="!canSubmit"
            class="w-full py-3 shadow-lg shadow-blue-600/20"
          >
            Finalizar OS
          </BaseButton>
        </div>
      </div>
    </form>

    <template #footer><span></span></template>
  </BaseModal>

  <!-- ═══════════ Modal de detalhes do pagamento (aninhado) ═══════════ -->
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
          <p class="font-bold text-lg text-zinc-800">{{ getPaymentDisplayName(currentPaymentMethod.nome) }}</p>
          <p class="text-xs text-zinc-500">Restante: {{ formatCurrency(restante) }}</p>
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

      <div v-if="getMethodTipo(currentPaymentMethod).includes('CARTAO')" class="space-y-3">
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

        <!-- Juros por pagamento -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-center gap-3">
            <label class="text-sm font-medium text-zinc-600 flex items-center gap-1.5">
              <Percent :size="14" />
              Juros (%)
            </label>
            <div class="w-24">
              <BaseInput
                v-model="paymentDetails.taxa_juros"
                type="number"
                placeholder="0"
              />
            </div>
          </div>
          <div v-if="paymentDetails.taxa_juros > 0" class="flex justify-between text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg">
            <span>Valor com juros</span>
            <span class="font-semibold">
              {{ formatCurrency(Math.round(paymentValueReais * 100 * (1 + paymentDetails.taxa_juros / 100))) }}
            </span>
          </div>
        </div>
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

    <template #footer><span></span></template>
  </BaseModal>
</template>
