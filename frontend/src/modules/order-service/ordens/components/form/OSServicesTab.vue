<script setup lang="ts">
import { Plus, Trash2, Package, Wrench, ShoppingBag, Receipt } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { OsItemCreateSchemaDataType, OsItemReadSchemaDataType } from '../../schemas/relationship/osItem.schema';

type OsItem = OsItemCreateSchemaDataType | OsItemReadSchemaDataType;

interface Props {
  itens: OsItem[];
  isLocked?: boolean;
  subtotal: number;
  valorDesconto: number;
  valorTotal: number;
  valorEntrada?: number;
}

const props = withDefaults(defineProps<Props>(), {
  isLocked: false,
  valorEntrada: 0,
});

const emit = defineEmits<{
  addItem: [];
  editItem: [index: number];
  removeItem: [index: number];
}>();

function getItemIcon(item: OsItem) {
  return item.tipo === 'SERVICO' ? Wrench : ShoppingBag;
}

function getItemIconClass(item: OsItem) {
  return item.tipo === 'SERVICO'
    ? 'bg-brand-primary-light text-brand-primary'
    : 'bg-orange-50 text-orange-600';
}

function getItemTotal(item: OsItem): number {
  if ('valor_total' in item && item.valor_total !== undefined) return item.valor_total;
  return item.quantidade * item.valor_unitario;
}
</script>

<template>
  <div class="space-y-4 animate-fadeIn">
    <div class="flex items-center justify-between border-b border-slate-200 pb-3">
      <div class="flex items-center gap-3">
        <div class="bg-brand-primary-light p-2 rounded-lg text-brand-primary">
          <Package :size="20" />
        </div>
        <div>
          <h5 class="text-sm font-bold text-slate-700">Itens da OS</h5>
          <p class="text-xs text-slate-500">Serviços e Peças adicionados</p>
        </div>
      </div>

      <BaseButton v-if="!isLocked" variant="primary" size="sm" @click="emit('addItem')">
        <Plus :size="16" class="mr-2" />
        ADICIONAR ITEM
      </BaseButton>
    </div>

    <fieldset :disabled="isLocked" class="contents">
      <div
        v-if="itens.length === 0"
        class="flex flex-col items-center justify-center py-12 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50"
      >
        <div class="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mb-3">
          <Package :size="28" stroke-width="1.5" class="text-slate-300" />
        </div>
        <p class="text-sm font-semibold text-slate-500">Nenhum item adicionado</p>
        <p class="text-xs text-slate-400 mt-1">Clique em "Adicionar Item" para incluir serviços ou peças.</p>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="(item, index) in itens"
          :key="index"
          class="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg hover:border-brand-primary/20 transition-colors group"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" :class="getItemIconClass(item)">
              <component :is="getItemIcon(item)" :size="18" />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-bold text-slate-700 truncate">{{ item.nome }}</p>
              <p class="text-xs text-slate-500 truncate">{{ item.unidade_medida }}</p>
            </div>
          </div>

          <div class="flex items-center gap-6 shrink-0">
            <div class="text-right hidden sm:block">
              <p class="text-xs text-slate-400 font-medium uppercase">Qtd</p>
              <p class="text-sm font-bold text-slate-600">{{ item.quantidade }}</p>
            </div>
            <div class="text-right hidden sm:block">
              <p class="text-xs text-slate-400 font-medium uppercase">Unitário</p>
              <p class="text-sm font-bold text-slate-600">{{ formatCurrency(item.valor_unitario) }}</p>
            </div>
            <div class="text-right w-24">
              <p class="text-xs text-slate-400 font-medium uppercase">Total</p>
              <p class="text-sm font-black text-slate-800">{{ formatCurrency(getItemTotal(item)) }}</p>
            </div>

            <div v-if="!isLocked" class="flex items-center gap-1 pl-2 border-l border-slate-100">
              <BaseButton variant="ghost" size="sm" class="p-1.5 text-slate-400 hover:text-brand-primary hover:bg-brand-primary-light" @click="emit('editItem', index)">
                <Wrench :size="14" />
              </BaseButton>
              <BaseButton variant="ghost" size="sm" class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50" @click="emit('removeItem', index)">
                <Trash2 :size="14" />
              </BaseButton>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-slate-50 rounded-xl p-4 border border-slate-200 mt-4">
        <div class="flex items-center gap-3 mb-4">
          <Receipt :size="20" class="text-slate-500" />
          <div>
            <span class="text-xs text-slate-500 font-medium">Resumo Financeiro</span>
            <p class="text-sm text-slate-600">{{ itens.length }} {{ itens.length === 1 ? 'item' : 'itens' }} lançados</p>
          </div>
        </div>

        <div class="space-y-2 border-t border-slate-200 pt-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-slate-600">Subtotal</span>
            <span class="font-semibold text-slate-700">{{ formatCurrency(subtotal) }}</span>
          </div>

          <div v-if="valorDesconto > 0" class="flex items-center justify-between text-sm">
            <span class="text-red-600">Desconto Aplicado</span>
            <span class="font-semibold text-red-600">- {{ formatCurrency(valorDesconto) }}</span>
          </div>

          <div v-if="(valorEntrada || 0) > 0" class="flex items-center justify-between text-sm">
            <span class="text-emerald-600">Entrada / Sinal</span>
            <span class="font-semibold text-emerald-600">{{ formatCurrency(valorEntrada || 0) }}</span>
          </div>

          <div class="border-t border-slate-300 my-2"></div>

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
