<script setup lang="ts">
import { computed } from 'vue';
import { Receipt, Wrench, ShoppingBag, Banknote } from 'lucide-vue-next';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { OsItemCreateSchemaDataType, OsItemReadSchemaDataType } from '../../schemas/relationship/osItem.schema';

type OsItem = OsItemCreateSchemaDataType | OsItemReadSchemaDataType;

interface Props {
  itens: OsItem[];
  subtotal: number;
  valorDesconto: number;
  valorTotal: number;
  valorEntrada: number;
  isLocked: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  valorEntrada: 0,
});

const emit = defineEmits<{
  'update:valorEntrada': [value: number];
}>();

const servicosCount = computed(() => props.itens.filter(i => i.tipo === 'SERVICO').length);
const produtosCount = computed(() => props.itens.filter(i => i.tipo === 'PRODUTO').length);

const valorEntradaReais = computed({
  get: () => (props.valorEntrada || 0) / 100,
  set: (val: number) => emit('update:valorEntrada', Math.round((val || 0) * 100)),
});

const restante = computed(() => Math.max(0, props.valorTotal - (props.valorEntrada || 0)));

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
        <div class="flex items-center justify-between text-sm">
          <span class="text-slate-500">Subtotal</span>
          <span class="font-semibold text-slate-700">{{ formatCurrency(subtotal) }}</span>
        </div>

        <div v-if="valorDesconto > 0" class="flex items-center justify-between text-sm">
          <span class="text-red-500">Desconto</span>
          <span class="font-semibold text-red-500">- {{ formatCurrency(valorDesconto) }}</span>
        </div>

        <!-- Adiantamento / Entrada -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5">
            <Banknote :size="14" class="text-emerald-500" />
            <span class="text-sm text-emerald-600 font-medium">Entrada</span>
          </div>
          <div class="w-28">
            <BaseMoneyInput
              v-model="valorEntradaReais"
              :disabled="isLocked"
              class="text-right text-sm"
            />
          </div>
        </div>

        <div class="border-t border-slate-300 my-1"></div>

        <div class="flex items-center justify-between">
          <span class="text-slate-800 font-bold text-sm">Valor a Pagar</span>
          <span class="text-lg font-black text-slate-800">{{ formatCurrency(restante) }}</span>
        </div>
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
