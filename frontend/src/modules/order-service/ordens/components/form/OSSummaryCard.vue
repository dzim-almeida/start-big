<script setup lang="ts">
import { computed } from 'vue';
import { Receipt, Wrench, ShoppingBag, Banknote, CreditCard, Wallet, QrCode, FileText, Truck, CheckCircle2 } from 'lucide-vue-next';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { OsItemCreateSchemaDataType, OsItemReadSchemaDataType } from '../../schemas/relationship/osItem.schema';
import type { OsPaymentReadSchemaDataType } from '../../schemas/relationship/osPayment.schema';
import { inferPaymentType, getPaymentDisplayName } from '@/shared/utils/print.utils';

type OsItem = OsItemCreateSchemaDataType | OsItemReadSchemaDataType;

interface Props {
  itens: OsItem[];
  subtotal: number;
  valorEntrega: number;
  valorDesconto: number;
  valorTotal: number;
  valorEntrada: number;
  valorAcrescimo?: number;
  isLocked: boolean;
  isFinalizada?: boolean;
  pagamentos?: OsPaymentReadSchemaDataType[];
  creditoAoReabrir?: number | null;
  saldoCreditoCliente?: number;
}

const props = withDefaults(defineProps<Props>(), {
  valorEntrada: 0,
  valorAcrescimo: 0,
  isFinalizada: false,
  pagamentos: () => [],
});

function getPaymentIcon(tipo: string) {
  switch (tipo) {
    case 'DINHEIRO':       return Banknote;
    case 'PIX':            return QrCode;
    case 'CARTAO_CREDITO': return CreditCard;
    case 'CARTAO_DEBITO':  return Wallet;
    case 'BOLETO':         return FileText;
    default:               return Banknote;
  }
}

const totalRecebido = computed(() =>
  (props.pagamentos ?? []).reduce((sum, p) => sum + p.valor, 0)
);

// Quanto do adiantamento foi consumido pelo valor do serviço (só em OS finalizada)
const adiantamentoUtilizado = computed(() => {
  if (!props.isFinalizada || !props.valorEntrada || !props.valorTotal) return 0;
  return Math.min(props.valorEntrada, props.valorTotal);
});

// Só muda o "Valor Pago" quando o adiantamento cobriu tudo e não há pagamentos adicionais
// Nos outros casos mantém o comportamento atual (restante) para não quebrar nada
const valorPagoDisplay = computed(() => {
  if (props.isFinalizada && adiantamentoUtilizado.value > 0 && totalRecebido.value === 0) {
    return adiantamentoUtilizado.value;
  }
  return restante.value;
});

// Troco só faz sentido em OS FINALIZADA (já foi calculado e entregue ao cliente)
// Em OS reaberta com pagamentos anteriores, o troco já foi dado — não exibir
const troco = computed(() => {
  if (!props.isFinalizada) return 0;
  return Math.max(0, totalRecebido.value - restante.value);
});

const emit = defineEmits<{
  'update:valorEntrada': [value: number];
  'update:valorEntrega': [value: number];
  'usarCredito': [];
}>();

const servicosCount = computed(() => props.itens.filter(i => i.tipo === 'SERVICO').length);
const produtosCount = computed(() => props.itens.filter(i => i.tipo === 'PRODUTO').length);

const totalServicos = computed(() => props.itens.filter(i => i.tipo === 'SERVICO').reduce((acc, curr) => acc + getItemTotal(curr), 0));
const totalProdutos = computed(() => props.itens.filter(i => i.tipo === 'PRODUTO').reduce((acc, curr) => acc + getItemTotal(curr), 0));

const valorEntradaReais = computed({
  get: () => (props.valorEntrada || 0) / 100,
  set: (val: number) => emit('update:valorEntrada', Math.round((val || 0) * 100)),
});

const valorEntregaReais = computed({
  get: () => (props.valorEntrega || 0) / 100,
  set: (val: number) => emit('update:valorEntrega', Math.round((val || 0) * 100)),
});

const totalPagamentosAnteriores = computed(() => {
  const raw = (props.pagamentos ?? []).reduce((sum, p) => sum + p.valor, 0);
  if (props.creditoAoReabrir != null) {
    const acrescimoAnterior = props.valorAcrescimo ?? 0;
    return Math.min(raw, Math.max(0, props.creditoAoReabrir - acrescimoAnterior));
  }
  return raw;
});

const restante = computed(() => {
  let base = Math.max(0, props.valorTotal - (props.valorEntrada || 0));
  if (!props.isFinalizada && totalPagamentosAnteriores.value > 0) {
    // Em OS reaberta, o acrescimo antigo já está no valor_total do banco mas já foi pago —
    // subtrai para que não seja cobrado novamente do cliente
    const acrescimoAnterior = props.valorAcrescimo ?? 0;
    base = Math.max(0, base - acrescimoAnterior);
    return Math.max(0, base - totalPagamentosAnteriores.value);
  }
  return base;
});

function getItemTotal(item: OsItem): number {
  if ('valor_total' in item && item.valor_total !== undefined) return item.valor_total;
  return item.quantidade * item.valor_unitario;
}
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="bg-slate-50 px-4 py-2.5 border-b border-slate-100 flex items-center gap-2">
      <Receipt :size="14" class="text-brand-primary" />
      <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Resumo da OS</span>
    </div>

    <div class="p-4 space-y-4">
      <!-- Contadores -->
      <div class="flex items-center gap-2">
        <span
          v-if="servicosCount > 0"
          class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-brand-primary-light text-brand-primary"
        >
          <Wrench :size="12" />
          {{ servicosCount }} {{ servicosCount === 1 ? 'Serviço' : 'Serviços' }}
        </span>
        <span
          v-if="produtosCount > 0"
          class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-brand-primary-light text-brand-primary"
        >
          <ShoppingBag :size="12" />
          {{ produtosCount }} {{ produtosCount === 1 ? 'Produto' : 'Produtos' }}
        </span>
        <span
          v-if="itens.length === 0"
          class="text-xs text-slate-400 italic"
        >
          Nenhum item adicionado
        </span>
      </div>

      <!-- Lista compacta de itens -->
      <div v-if="itens.length > 0" class="max-h-36 overflow-y-auto space-y-1 custom-scrollbar">
        <div
          v-for="(item, index) in itens"
          :key="index"
          class="flex items-center justify-between py-1.5 px-2 rounded-md hover:bg-slate-50 transition-colors"
        >
          <div class="flex items-center gap-2 min-w-0">
            <component
              :is="item.tipo === 'SERVICO' ? Wrench : ShoppingBag"
              :size="12"
              class="text-brand-primary shrink-0"
            />
            <span class="text-xs text-slate-600 truncate">{{ item.nome }}</span>
          </div>
          <div class="flex items-center gap-3 shrink-0 ml-2">
            <span class="text-[10px] text-slate-400">×{{ item.quantidade }}</span>
            <span class="text-xs font-bold text-slate-700 w-20 text-right">{{ formatCurrency(getItemTotal(item)) }}</span>
          </div>
        </div>
      </div>

      <!-- Resumo financeiro -->
      <div class="border-t border-slate-200 pt-3 space-y-2">
        <div v-if="servicosCount > 0" class="flex items-center justify-between text-sm">
          <span class="text-slate-500">Mão-de-obra</span>
          <span class="font-medium text-slate-700">{{ formatCurrency(totalServicos) }}</span>
        </div>

        <div v-if="produtosCount > 0" class="flex items-center justify-between text-sm">
          <span class="text-slate-500">Peças</span>
          <span class="font-medium text-slate-700">{{ formatCurrency(totalProdutos) }}</span>
        </div>

        <div class="flex items-center justify-between text-sm pt-1 border-t border-slate-100 border-dashed">
          <span class="text-slate-500 font-medium">Subtotal</span>
          <span class="font-semibold text-brand-primary">{{ formatCurrency(subtotal) }}</span>
        </div>

        <div v-if="valorDesconto > 0" class="flex items-center justify-between text-sm">
          <span class="text-red-500">Desconto</span>
          <span class="font-semibold text-red-500">- {{ formatCurrency(valorDesconto) }}</span>
        </div>

        <!-- Juros só aparece quando finalizada ou em OS nova (sem crédito anterior) -->
        <!-- Em OS reaberta os juros antigos já foram pagos, não são dívida atual -->
        <div v-if="valorAcrescimo > 0 && (isFinalizada || !creditoAoReabrir)" class="flex items-center justify-between text-sm">
          <span class="text-amber-600">Juros</span>
          <span class="font-semibold text-amber-600">+ {{ formatCurrency(valorAcrescimo) }}</span>
        </div>

        <!-- Adiantamento / Entrada — esconde quando finalizada e zerado -->
        <div v-if="!isFinalizada || valorEntrada > 0" class="flex items-center justify-between gap-2 pt-2">
          <div class="flex items-center gap-1.5">
            <Banknote :size="14" class="text-emerald-500" />
            <span class="text-sm text-emerald-600 font-medium">Adiantamento</span>
          </div>
          <div class="w-28">
            <BaseMoneyInput
              v-model="valorEntradaReais"
              :disabled="isLocked"
              class="text-sm"
              input-class="text-right"
            />
          </div>
        </div>

        <!-- Crédito disponível do cliente -->
        <div
          v-if="!isFinalizada && !isLocked && (saldoCreditoCliente ?? 0) > 0 && valorEntrada < (saldoCreditoCliente ?? 0)"
          class="flex items-center justify-between gap-2"
        >
          <span class="text-xs text-emerald-600 font-medium">
            Crédito disponível: {{ formatCurrency(saldoCreditoCliente ?? 0) }}
          </span>
          <button
            type="button"
            class="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-300 hover:bg-emerald-100 px-2 py-0.5 rounded-full transition-colors"
            @click="emit('usarCredito')"
          >
            Usar crédito
          </button>
        </div>

        <!-- Deslocamento / Frete — esconde quando finalizada e zerado -->
        <div v-if="!isFinalizada || valorEntrega > 0" class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5">
            <Truck :size="14" class="text-slate-400" />
            <span class="text-sm text-slate-500 font-medium">Deslocamento</span>
          </div>
          <div class="w-28">
            <BaseMoneyInput
              v-model="valorEntregaReais"
              :disabled="isLocked"
              class="text-sm"
              input-class="text-right"
            />
          </div>
        </div>

        <div class="border-t border-slate-300 my-1"></div>

        <div class="flex items-center justify-between">
          <span class="text-slate-800 font-bold text-sm">
            {{ isFinalizada ? 'Valor Pago' : (pagamentos && pagamentos.length > 0 ? 'Restante a Pagar' : 'Valor a Pagar') }}
          </span>
          <span class="text-lg font-black text-slate-800">{{ formatCurrency(isFinalizada ? valorPagoDisplay : restante) }}</span>
        </div>
      </div>

      <!-- Pagamentos históricos -->
      <div v-if="(pagamentos && pagamentos.length > 0) || adiantamentoUtilizado > 0" class="border-t border-slate-200 pt-3 space-y-2">
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">
          {{ isFinalizada ? 'Pagamentos Recebidos' : 'Crédito Anterior' }}
        </p>

        <!-- OS FINALIZADA: mostra cada pagamento com valor real + troco -->
        <template v-if="isFinalizada">
          <!-- Adiantamento aplicado: aparece quando o adiantamento cobriu parte ou tudo -->
          <div v-if="adiantamentoUtilizado > 0 && pagamentos.length === 0" class="flex items-center justify-between py-1">
            <div class="flex items-center gap-2">
              <div class="p-1 bg-emerald-50 rounded-md text-emerald-600">
                <Banknote :size="11" />
              </div>
              <p class="text-xs font-medium text-slate-700">Adiantamento aplicado</p>
            </div>
            <span class="text-xs font-semibold text-emerald-600">{{ formatCurrency(adiantamentoUtilizado) }}</span>
          </div>

          <div
            v-for="pgto in pagamentos"
            :key="pgto.id"
            class="flex items-center justify-between py-1"
          >
            <div class="flex items-center gap-2">
              <div class="p-1 bg-brand-primary/10 rounded-md text-brand-primary">
                <component :is="getPaymentIcon(inferPaymentType(pgto.forma_pagamento.nome))" :size="11" />
              </div>
              <div>
                <p class="text-xs font-medium text-slate-700">{{ getPaymentDisplayName(pgto.forma_pagamento.nome) }}</p>
                <p v-if="pgto.parcelas > 1" class="text-[10px] text-slate-400">{{ pgto.parcelas }}x</p>
              </div>
            </div>
            <span class="text-xs font-semibold text-slate-700">{{ formatCurrency(pgto.valor) }}</span>
          </div>
          <div v-if="troco > 0" class="flex items-center justify-between pt-1 border-t border-dashed border-slate-200">
            <span class="text-xs font-medium text-amber-500">Troco</span>
            <span class="text-xs font-semibold text-amber-500">{{ formatCurrency(troco) }}</span>
          </div>

          <!-- Breakdown de devolução (só exibe quando há juros) -->
          <div v-if="(valorAcrescimo ?? 0) > 0" class="mt-2 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-2 space-y-1">
            <p class="text-[10px] font-semibold text-amber-700 uppercase tracking-wide">Em caso de devolução</p>
            <div class="flex justify-between items-center text-[10px] text-zinc-600">
              <span>Serviço (dinheiro)</span>
              <span class="font-semibold">{{ formatCurrency(totalRecebido - (valorAcrescimo ?? 0)) }}</span>
            </div>
            <div class="flex justify-between items-center text-[10px] text-zinc-600">
              <span>Estorno cartão</span>
              <span class="font-semibold">{{ formatCurrency(totalRecebido) }}</span>
            </div>
            <p class="text-[10px] text-amber-600">Juros à operadora: {{ formatCurrency(valorAcrescimo ?? 0) }}</p>
          </div>
        </template>

        <!-- OS REABERTA: mostra só o crédito efetivo (valor cobrado, sem troco) -->
        <template v-else>
          <div class="flex items-center justify-between py-1">
            <div class="flex items-center gap-2">
              <div class="p-1 bg-emerald-50 rounded-md text-emerald-600">
                <CheckCircle2 :size="11" />
              </div>
              <p class="text-xs font-medium text-slate-700">Já pago</p>
            </div>
            <span class="text-xs font-semibold text-emerald-600">{{ formatCurrency(totalPagamentosAnteriores) }}</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: #e4e4e7; border-radius: 20px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: #d4d4d8; }
</style>
