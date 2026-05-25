<script setup lang="ts">
import { PackageOpen } from 'lucide-vue-next';
import type { EstoqueBaixoItemData } from '../../schemas/dashboard.schema';

interface Props {
  items: EstoqueBaixoItemData[];
  isLoading: boolean;
  isError: boolean;
}

defineProps<Props>();

const statusConfig = {
  zerado: {
    label: 'Zerado',
    class: 'bg-red-50 text-red-600 border border-red-200',
  },
  baixo: {
    label: 'Baixo',
    class: 'bg-amber-50 text-amber-600 border border-amber-200',
  },
};
</script>

<template>
  <div class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-2">
      <PackageOpen :size="18" class="text-zinc-500" />
      <h3 class="font-bold text-base md:text-lg text-zinc-900">Alerta de Estoque</h3>
    </div>

    <!-- Error -->
    <div v-if="isError" class="p-8 text-center text-red-500 text-sm">
      Erro ao carregar estoque
    </div>

    <!-- Loading -->
    <div v-else-if="isLoading" class="p-6 space-y-3">
      <div v-for="i in 3" :key="i" class="h-10 bg-zinc-100 rounded-lg animate-pulse" />
    </div>

    <!-- Table -->
    <div v-else-if="items.length > 0" class="overflow-x-auto">
      <table class="w-full text-left">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 py-3">Produto</th>
            <th class="px-4 py-3 text-center">Qtd</th>
            <th class="px-4 py-3 text-right">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="item in items"
            :key="item.produto_id"
            class="hover:bg-zinc-50/50 transition-colors"
          >
            <td class="px-4 py-2.5 text-xs md:text-sm font-semibold text-zinc-700">
              <span class="block truncate max-w-32 md:max-w-44">{{ item.nome }}</span>
            </td>
            <td
              :class="[
                'px-4 py-2.5 text-xs md:text-sm font-bold text-center',
                item.quantidade === 0 ? 'text-red-600' : 'text-amber-600',
              ]"
            >
              {{ item.quantidade }}
            </td>
            <td class="px-4 py-2.5 text-right">
              <span
                :class="[
                  'px-2 py-0.5 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  statusConfig[item.status].class,
                ]"
              >
                {{ statusConfig[item.status].label }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-else class="p-8 text-center text-zinc-400 text-sm">
      Estoque em dia
    </div>
  </div>
</template>
