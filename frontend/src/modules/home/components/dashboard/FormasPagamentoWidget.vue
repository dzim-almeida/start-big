<script setup lang="ts">
import { CreditCard } from 'lucide-vue-next';
import { formatCurrency } from '@/shared/utils/finance';
import type { FormaPagamentoItemData } from '../../schemas/dashboard.schema';

interface Props {
  items: FormaPagamentoItemData[];
  total: number;
  isLoading: boolean;
  isError: boolean;
}

defineProps<Props>();

function percentual(valor: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((valor / total) * 100);
}
</script>

<template>
  <div class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-hidden flex flex-col">
    <div class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-2">
      <CreditCard :size="18" class="text-zinc-500" />
      <h3 class="font-bold text-base md:text-lg text-zinc-900">Formas de Pagamento</h3>
      <span v-if="total > 0" class="ml-auto text-xs font-semibold text-zinc-400">
        {{ formatCurrency(total) }} total
      </span>
    </div>

    <div v-if="isError" class="p-8 text-center text-red-500 text-sm flex-1 flex items-center justify-center">
      Erro ao carregar dados
    </div>

    <div v-else-if="isLoading" class="p-6 space-y-4 flex-1">
      <div v-for="i in 4" :key="i" class="h-10 bg-zinc-100 rounded-lg animate-pulse" />
    </div>

    <div v-else-if="items.length > 0" class="p-4 md:p-6 space-y-4 flex-1">
      <div v-for="item in items" :key="item.nome" class="space-y-1.5">
        <div class="flex items-center justify-between text-sm">
          <span class="font-medium text-zinc-700">{{ item.nome }}</span>
          <span class="font-semibold text-zinc-800">{{ formatCurrency(item.valor_total) }}</span>
        </div>
        <div class="h-1.5 bg-zinc-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-zinc-800 rounded-full transition-all duration-500"
            :style="{ width: `${percentual(item.valor_total, total)}%` }"
          />
        </div>
      </div>
    </div>

    <div v-else class="p-8 text-center text-zinc-400 text-sm flex-1 flex items-center justify-center">
      Nenhum pagamento no período
    </div>
  </div>
</template>
