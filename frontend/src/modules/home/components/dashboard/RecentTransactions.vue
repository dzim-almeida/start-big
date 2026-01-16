<script setup lang="ts">
import type { Transaction } from '../../types/dashboard.types';

interface Props {
  transactions: Transaction[];
}

defineProps<Props>();

const statusConfig = {
  completed: {
    label: 'Concluído',
    class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
  },
  pending: {
    label: 'Pendente',
    class: 'bg-amber-50 text-amber-600 border border-amber-200',
  },
  cancelled: {
    label: 'Cancelado',
    class: 'bg-red-50 text-red-600 border border-red-200',
  },
};

function getInitial(name: string): string {
  return name.charAt(0).toUpperCase();
}
</script>

<template>
  <div
    class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-hidden"
  >
    <!-- Header -->
    <div class="p-4 md:p-6 border-b border-zinc-100 flex justify-between items-center">
      <h3 class="font-bold text-base md:text-lg text-zinc-900">Últimas Transações</h3>
      <button
        class="text-brand-primary text-xs md:text-sm font-semibold hover:underline transition-all hover:text-brand-primary/80"
      >
        Ver todas
      </button>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-125">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">ID Pedido</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Cliente</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Valor</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="transaction in transactions"
            :key="transaction.id"
            class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
          >
            <!-- ID -->
            <td
              class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-400 group-hover:text-zinc-900 transition-colors"
            >
              {{ transaction.id }}
            </td>

            <!-- Customer -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center gap-2 text-xs md:text-sm font-semibold">
                <div
                  class="w-6 h-6 md:w-7 md:h-7 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center text-[10px] md:text-[11px] font-bold"
                >
                  {{ getInitial(transaction.customer) }}
                </div>
                <span class="truncate max-w-30 md:max-w-none">{{
                  transaction.customer
                }}</span>
              </div>
            </td>

            <!-- Value -->
            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-bold text-zinc-900">
              {{ transaction.value }}
            </td>

            <!-- Status -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  statusConfig[transaction.status].class,
                ]"
              >
                {{ statusConfig[transaction.status].label }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div
      v-if="transactions.length === 0"
      class="p-8 text-center text-zinc-400 text-sm"
    >
      Nenhuma transação encontrada
    </div>
  </div>
</template>
