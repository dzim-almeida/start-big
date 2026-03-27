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
  Package,
  Percent,
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
const paymentDetails = ref<{ valor: number; parcelas: number; bandeira: OsCardsFlagEnumDataType | '' }>({ valor: 0, parcelas: 1, bandeira: '' });

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
  finalizarForm.desconto.value = Math.round(val * 100);
});

const taxaEntregaDisplay = ref(0);
watch(taxaEntregaDisplay, (val) => {
  finalizarForm.taxa_entrega.value = Math.round(val * 100);
});

// ─── Cálculos financeiros ─────────────────────────────────────────────────
const subtotalItens = computed(() => {
  if (!props.ordemServico?.itens) return 0;
  return props.ordemServico.itens.reduce((sum, item) => sum + item.valor_total, 0);
});

const itensProdutos = computed(() =>
  props.ordemServico?.itens.filter(i => i.tipo === 'PRODUTO') ?? [],
);
const itensServicos = computed(() =>
  props.ordemServico?.itens.filter(i => i.tipo === 'SERVICO') ?? [],
);
const subtotalProdutos = computed(() =>
  itensProdutos.value.reduce((sum, item) => sum + item.valor_total, 0),
);
const subtotalServicos = computed(() =>
  itensServicos.value.reduce((sum, item) => sum + item.valor_total, 0),
);

// ─── Acréscimo de juros (cartão) ──────────────────────────────────────────
const acrescimoPercentual = ref(0);

const hasCartaoPagamento = computed(() =>
  finalizarForm.pagamentos.value.some((p) => {
    const method = getPaymentMethodById(p.value.forma_pagamento_id);
    if (!method) return false;
    const tipo = getMethodTipo(method);
    return tipo === 'CARTAO_CREDITO' || tipo === 'CARTAO_DEBITO';
  }),
);

const baseParaAcrescimo = computed(() =>
  Math.max(0, subtotalItens.value - (finalizarForm.desconto.value ?? 0) + (finalizarForm.taxa_entrega.value ?? 0)),
);

const acrescimoCalculado = computed(() =>
  Math.round(baseParaAcrescimo.value * (acrescimoPercentual.value / 100)),
);

watch(acrescimoCalculado, (val) => {
  finalizarForm.acrescimo.value = val;
});

watch(hasCartaoPagamento, (has) => {
  if (!has) {
    acrescimoPercentual.value = 0;
    finalizarForm.acrescimo.value = 0;
  }
});

watch(acrescimoPercentual, (v) => {
  const clamped = Math.min(100, Math.max(0, v ?? 0));
  if (v !== clamped) acrescimoPercentual.value = clamped;
});

// ─── Reset ao fechar ──────────────────────────────────────────────────────
watch(() => props.isOpen, (open) => {
  if (!open) {
    hasAttemptedSubmit.value = false;
    finalizarForm.resetForm();
    descontoDisplay.value = 0;
    taxaEntregaDisplay.value = 0;
    acrescimoPercentual.value = 0;
    shouldPrint.value = false;
    confirmacao.value = false;
    showPaymentDetails.value = false;
    currentPaymentMethod.value = null;
  }
});

const valorTotal = computed(() => {
  const desc = finalizarForm.desconto.value ?? 0;
  const entrega = finalizarForm.taxa_entrega.value ?? 0;
  const acresc = finalizarForm.acrescimo.value ?? 0;
  return Math.max(0, subtotalItens.value - desc + entrega + acresc);
});

const valorEntrada = computed(() => props.ordemServico?.valor_entrada ?? 0);
const valorAPagar = computed(() => Math.max(0, valorTotal.value - valorEntrada.value));

const totalPago = computed(() =>
  finalizarForm.pagamentos.value.reduce((sum, p) => sum + (p.value.valor ?? 0), 0),
);

const restante = computed(() => Math.max(0, valorAPagar.value - totalPago.value));
const troco = computed(() => Math.max(0, totalPago.value - valorAPagar.value));

const canSubmit = computed(() =>
  confirmacao.value &&
  (finalizarForm.solucao.value?.trim().length ?? 0) >= 5 &&
  totalPago.value >= valorAPagar.value,
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

        <!-- Tabela de itens agrupada por tipo -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <Package :size="18" class="text-zinc-500" />
            <h3 class="text-sm font-semibold text-zinc-700">Itens da OS</h3>
            <span class="text-xs text-zinc-400">({{ ordemServico?.itens.length ?? 0 }})</span>
          </div>

          <div v-if="ordemServico?.itens && ordemServico.itens.length > 0" class="space-y-3">
            <!-- Grupo: Serviços -->
            <div v-if="itensServicos.length > 0" class="border border-zinc-200 rounded-xl overflow-hidden">
              <div class="bg-zinc-50 px-3 py-2 border-b border-zinc-100 flex items-center gap-2">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-brand-primary-light text-brand-primary">
                  <Wrench :size="12" />
                  {{ itensServicos.length }} {{ itensServicos.length === 1 ? 'Serviço' : 'Serviços' }}
                </span>
              </div>
              <table class="w-full text-sm">
                <thead class="bg-zinc-50/50">
                  <tr>
                    <th class="text-left px-3 py-1.5 font-medium text-zinc-500 text-xs">Item</th>
                    <th class="text-center px-3 py-1.5 font-medium text-zinc-500 text-xs w-14">Qtd</th>
                    <th class="text-right px-3 py-1.5 font-medium text-zinc-500 text-xs w-24">Unitário</th>
                    <th class="text-right px-3 py-1.5 font-medium text-zinc-500 text-xs w-24">Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-100">
                  <tr v-for="item in itensServicos" :key="item.id" class="hover:bg-zinc-50/50">
                    <td class="px-3 py-2 text-zinc-700">{{ item.nome }}</td>
                    <td class="px-3 py-2 text-center text-zinc-500">{{ item.quantidade }}</td>
                    <td class="px-3 py-2 text-right text-zinc-500">{{ formatCurrency(item.valor_unitario) }}</td>
                    <td class="px-3 py-2 text-right font-medium text-zinc-700">{{ formatCurrency(item.valor_total) }}</td>
                  </tr>
                </tbody>
                <tfoot class="bg-zinc-50 border-t border-zinc-200">
                  <tr>
                    <td colspan="3" class="px-3 py-1.5 text-right text-xs font-semibold text-zinc-500">Subtotal Serviços</td>
                    <td class="px-3 py-1.5 text-right text-sm font-bold text-zinc-700">{{ formatCurrency(subtotalServicos) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <!-- Grupo: Produtos -->
            <div v-if="itensProdutos.length > 0" class="border border-zinc-200 rounded-xl overflow-hidden">
              <div class="bg-zinc-50 px-3 py-2 border-b border-zinc-100 flex items-center gap-2">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-brand-primary-light text-brand-primary">
                  <ShoppingBag :size="12" />
                  {{ itensProdutos.length }} {{ itensProdutos.length === 1 ? 'Produto' : 'Produtos' }}
                </span>
              </div>
              <table class="w-full text-sm">
                <thead class="bg-zinc-50/50">
                  <tr>
                    <th class="text-left px-3 py-1.5 font-medium text-zinc-500 text-xs">Item</th>
                    <th class="text-center px-3 py-1.5 font-medium text-zinc-500 text-xs w-14">Qtd</th>
                    <th class="text-right px-3 py-1.5 font-medium text-zinc-500 text-xs w-24">Unitário</th>
                    <th class="text-right px-3 py-1.5 font-medium text-zinc-500 text-xs w-24">Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-100">
                  <tr v-for="item in itensProdutos" :key="item.id" class="hover:bg-zinc-50/50">
                    <td class="px-3 py-2 text-zinc-700">{{ item.nome }}</td>
                    <td class="px-3 py-2 text-center text-zinc-500">{{ item.quantidade }}</td>
                    <td class="px-3 py-2 text-right text-zinc-500">{{ formatCurrency(item.valor_unitario) }}</td>
                    <td class="px-3 py-2 text-right font-medium text-zinc-700">{{ formatCurrency(item.valor_total) }}</td>
                  </tr>
                </tbody>
                <tfoot class="bg-zinc-50 border-t border-zinc-200">
                  <tr>
                    <td colspan="3" class="px-3 py-1.5 text-right text-xs font-semibold text-zinc-500">Subtotal Produtos</td>
                    <td class="px-3 py-1.5 text-right text-sm font-bold text-zinc-700">{{ formatCurrency(subtotalProdutos) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <!-- Total geral dos itens -->
            <div class="flex justify-between items-center px-3 py-2.5 bg-zinc-100 rounded-xl">
              <span class="text-sm font-semibold text-zinc-600">Total dos Itens</span>
              <span class="text-sm font-bold text-zinc-800">{{ formatCurrency(subtotalItens) }}</span>
            </div>
          </div>

          <div v-else class="text-center py-6 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-sm text-zinc-400">Nenhum item na OS</p>
          </div>
        </div>

        <!-- Solução Aplicada -->
        <div>
          <div class="flex items-center gap-2 mb-2">
            <CheckCircle2 :size="18" class="text-emerald-600" />
            <label class="text-sm font-semibold text-zinc-700">Solução Aplicada <span class="text-red-500">*</span></label>
          </div>
          <BaseTextarea
            v-model="finalizarForm.solucao.value"
            placeholder="Descreva o serviço realizado, peças substituídas, testes efetuados..."
            :rows="4"
            :error="finalizarForm.errors.value.solucao"
          />
        </div>

        <!-- Observações -->
        <div>
          <label class="text-sm font-semibold text-zinc-700">Observações</label>
          <BaseTextarea
            v-model="finalizarForm.observacoes.value"
            :rows="2"
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
            <span class="text-zinc-500">Desconto</span>
            <div class="w-32">
              <BaseMoneyInput v-model="descontoDisplay" label="" />
            </div>
          </div>

          <!-- Juros Cartão (input percentual) -->
          <div class="flex justify-between items-center text-sm border-t border-zinc-200 pt-3">
            <span class="flex items-center gap-1.5" :class="hasCartaoPagamento ? 'text-zinc-500' : 'text-zinc-400'">
              <Percent :size="14" />
              Juros Cartão
            </span>
            <div class="flex items-center gap-2">
              <div class="w-20">
                <BaseInput
                  v-model="acrescimoPercentual"
                  type="number"
                  placeholder="0"
                  :disabled="!hasCartaoPagamento"
                />
              </div>
              <span class="text-[11px] text-zinc-400 whitespace-nowrap">%</span>
            </div>
          </div>
          <p v-if="!hasCartaoPagamento" class="text-[10px] text-zinc-400 -mt-1 text-right">
            Adicione pagamento via cartão para habilitar
          </p>

          <!-- Acréscimo Total (read-only) -->
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
              <span class="text-emerald-600">{{ formatCurrency(valorTotal) }}</span>
            </div>

            <!-- Entrada -->
            <div v-if="valorEntrada > 0" class="flex justify-between items-center text-sm text-emerald-600 font-medium mt-2">
              <span>Entrada / Adiantamento</span>
              <span>- {{ formatCurrency(valorEntrada) }}</span>
            </div>

            <!-- A Pagar -->
            <div v-if="valorEntrada > 0" class="flex justify-between items-center text-sm font-bold mt-1">
              <span class="text-zinc-700">A Pagar</span>
              <span class="text-zinc-800">{{ formatCurrency(valorAPagar) }}</span>
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

          <div v-if="finalizarForm.pagamentos.value.length === 0" class="text-center py-5 border-2 border-dashed border-zinc-200 rounded-xl">
            <p class="text-xs text-zinc-400">Nenhum pagamento registrado</p>
          </div>

          <div v-else class="space-y-2 max-h-40 overflow-y-auto">
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

        <!-- Grid de Formas de Pagamento -->
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="method in formasPagamento"
            :key="method.id"
            type="button"
            class="flex flex-col items-center justify-center p-2 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50 hover:border-emerald-500 hover:text-emerald-600 transition-all gap-1 h-16 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
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
            Finalizar OS ({{ formatCurrency(valorAPagar) }})
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
        <div class="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
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

    <template #footer><span></span></template>
  </BaseModal>
</template>
