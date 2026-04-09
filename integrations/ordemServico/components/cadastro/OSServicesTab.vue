<script setup lang="ts">
/**
 * OSServicesTab.vue
 * Aba de servicos e pecas da OS
 */
import {
  Plus,
  Trash2,
  Package,
  Wrench,
  ShoppingBag,
  Receipt,
} from 'lucide-vue-next';

import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { OSItemForm } from '../../composables/useOSFormState';

interface SelectOption {
  value: string;
  label: string;
}

interface Props {
  itens: OSItemForm[];
  servicosOptions: SelectOption[];
  produtosOptions: SelectOption[];
  isLoadingServicos?: boolean;
  isLoadingProdutos?: boolean;
  isLocked?: boolean;
  subtotal: number;
  valorDesconto: number;
  valorTaxaEntrega: number;
  valorTotal: number;
  valorEntrada?: string;
  taxaEntrega?: string;
  desconto?: string;
}

const props = withDefaults(defineProps<Props>(), {
  isLoadingServicos: false,
  isLoadingProdutos: false,
  isLocked: false,
  valorEntrada: '0',
  taxaEntrega: '',
  desconto: '',
});

const emit = defineEmits<{
  addItem: [];
  editItem: [index: number];
  removeItem: [index: number];
  'update:taxaEntrega': [value: string];
  'update:desconto': [value: string];
}>();

function handleCurrencyInput(e: Event, emitFn: 'update:taxaEntrega' | 'update:desconto') {
  const target = e.target as HTMLInputElement;
  let value = target.value.replace(/\D/g, '');
  if (!value) value = '0';
  const floatVal = parseFloat(value) / 100;
  const formatted = floatVal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  emit(emitFn, formatted);
}

function getItemIcon(item: OSItemForm) {
  return props.servicosOptions.some(s => s.value === item.servico_id) ? Wrench : ShoppingBag;
}

function getItemIconClass(item: OSItemForm) {
  return props.servicosOptions.some(s => s.value === item.servico_id)
    ? 'bg-brand-primary-light text-brand-primary'
    : 'bg-orange-50 text-orange-600';
}

function getItemLabel(item: OSItemForm, index: number) {
  return (
    props.servicosOptions.find(o => o.value === item.servico_id)?.label ||
    props.produtosOptions.find(o => o.value === item.servico_id)?.label ||
    `Item ${index + 1}`
  );
}
</script>

<template>
  <div class="space-y-4 animate-fadeIn">
    <!-- Header da Aba -->
    <div class="flex items-center justify-between border-b border-slate-200 pb-3">
      <div class="flex items-center gap-3">
        <div class="bg-brand-primary-light p-2 rounded-lg text-brand-primary">
          <Package :size="20" />
        </div>
        <div>
          <h5 class="text-sm font-bold text-slate-700">Itens da OS</h5>
          <p class="text-xs text-slate-500">Servicos e Pecas adicionados</p>
        </div>
      </div>

      <BaseButton
        v-if="!isLocked"
        variant="primary"
        size="sm"
        @click="emit('addItem')"
      >
        <Plus :size="16" class="mr-2" />
        ADICIONAR ITEM
      </BaseButton>
    </div>

    <fieldset :disabled="isLocked" class="contents">
      <!-- Loading -->
      <div
        v-if="isLoadingServicos || isLoadingProdutos"
        class="flex items-center justify-center py-8 text-slate-400"
      >
        <div class="animate-spin w-5 h-5 border-2 border-slate-300 border-t-emerald-500 rounded-full mr-2"></div>
        <span class="text-sm">Carregando catalogo...</span>
      </div>

      <!-- Lista Vazia -->
      <div
        v-else-if="itens.length === 0"
        class="flex flex-col items-center justify-center py-12 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50"
      >
        <div class="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mb-3">
          <Package :size="28" stroke-width="1.5" class="text-slate-300" />
        </div>
        <p class="text-sm font-semibold text-slate-500">Nenhum item adicionado</p>
        <p class="text-xs text-slate-400 mt-1">
          Clique em "Adicionar Item" para incluir servicos ou pecas.
        </p>
      </div>

      <!-- LISTA RESUMO DOS ITENS -->
      <div v-else class="space-y-2">
        <div
          v-for="(item, index) in itens"
          :key="index"
          class="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg hover:border-brand-primary/20 transition-colors group"
        >
          <!-- Esquerda: Icone + Descricao -->
          <div class="flex items-center gap-3 overflow-hidden">
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
              :class="getItemIconClass(item)"
            >
              <component :is="getItemIcon(item)" :size="18" />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-bold text-slate-700 truncate">
                {{ getItemLabel(item, index) }}
              </p>
              <p class="text-xs text-slate-500 truncate">
                {{ item.descricao || 'Sem descricao adicional' }}
              </p>
            </div>
          </div>

          <!-- Direita: Valores + Acoes -->
          <div class="flex items-center gap-6 shrink-0">
            <div class="text-right hidden sm:block">
              <p class="text-xs text-slate-400 font-medium uppercase">Qtd/Hr</p>
              <p class="text-sm font-bold text-slate-600">{{ item.quantidade }}</p>
            </div>
            <div class="text-right hidden sm:block">
              <p class="text-xs text-slate-400 font-medium uppercase">Unitario</p>
              <p class="text-sm font-bold text-slate-600">{{ formatCurrency(item.valor_unitario) }}</p>
            </div>
            <div class="text-right w-24">
              <p class="text-xs text-slate-400 font-medium uppercase">Total</p>
              <p class="text-sm font-black text-slate-800">
                {{ formatCurrency(item.quantidade * item.valor_unitario) }}
              </p>
            </div>

            <!-- Acoes -->
            <div v-if="!isLocked" class="flex items-center gap-1 pl-2 border-l border-slate-100">
              <BaseButton
                variant="ghost"
                size="sm"
                class="p-1.5 text-slate-400 hover:text-brand-primary hover:bg-brand-primary-light"
                @click="emit('editItem', index)"
              >
                <Wrench :size="14" />
              </BaseButton>
              <BaseButton
                variant="ghost"
                size="sm"
                class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50"
                @click="emit('removeItem', index)"
              >
                <Trash2 :size="14" />
              </BaseButton>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumo Financeiro Detalhado -->
      <div class="bg-slate-50 rounded-xl p-4 border border-slate-200 mt-4">
        <div class="flex items-center gap-3 mb-4">
          <Receipt :size="20" class="text-slate-500" />
          <div>
            <span class="text-xs text-slate-500 font-medium">Resumo Financeiro</span>
            <p class="text-sm text-slate-600">
              {{ itens.length }} {{ itens.length === 1 ? 'item' : 'itens' }} lancados
            </p>
          </div>
        </div>

        <!-- Detalhamento dos valores -->
        <div class="space-y-2 border-t border-slate-200 pt-3">
          <!-- Subtotal -->
          <div class="flex items-center justify-between text-sm">
            <span class="text-slate-600">Subtotal</span>
            <span class="font-semibold text-slate-700">{{ formatCurrency(subtotal) }}</span>
          </div>

          <!-- Taxa de Entrega (input editavel) -->
          <div class="flex items-center justify-between text-sm">
            <span class="text-blue-600">Taxa de Entrega</span>
            <div class="relative w-32">
              <span class="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-medium">R$</span>
              <input
                :value="taxaEntrega"
                type="text"
                :disabled="isLocked"
                class="w-full pl-7 pr-2 py-1 border rounded text-right text-sm font-semibold text-blue-600 border-slate-200 focus:border-blue-400 focus:ring-1 focus:ring-blue-400 bg-white outline-none disabled:bg-slate-100 disabled:text-slate-400"
                placeholder="0,00"
                @input="handleCurrencyInput($event, 'update:taxaEntrega')"
              />
            </div>
          </div>

          <!-- Desconto (input editavel) -->
          <div class="flex items-center justify-between text-sm">
            <span class="text-red-600">Desconto</span>
            <div class="relative w-32">
              <span class="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-medium">R$</span>
              <input
                :value="desconto"
                type="text"
                :disabled="isLocked"
                class="w-full pl-7 pr-2 py-1 border rounded text-right text-sm font-semibold text-red-600 border-slate-200 focus:border-red-400 focus:ring-1 focus:ring-red-400 bg-white outline-none disabled:bg-slate-100 disabled:text-slate-400"
                placeholder="0,00"
                @input="handleCurrencyInput($event, 'update:desconto')"
              />
            </div>
          </div>

          <!-- Entrada (so mostra se houver) -->
          <div
            v-if="parseFloat(valorEntrada || '0') > 0"
            class="flex items-center justify-between text-sm"
          >
            <span class="text-emerald-600">Entrada / Sinal</span>
            <span class="font-semibold text-emerald-600">- R$ {{ valorEntrada }}</span>
          </div>

          <!-- Linha separadora -->
          <div class="border-t border-slate-300 my-2"></div>

          <!-- Total Final -->
          <div class="flex items-center justify-between">
            <span class="text-slate-800 font-bold">Total Final</span>
            <span class="text-2xl font-black text-slate-800">{{ formatCurrency(valorTotal) }}</span>
          </div>
        </div>
      </div>
    </fieldset>
  </div>
</template>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
