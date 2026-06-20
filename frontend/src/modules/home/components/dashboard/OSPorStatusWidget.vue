<script setup lang="ts">
import { LayoutGrid } from 'lucide-vue-next';
import type { OSPorStatusItemData } from '../../schemas/dashboard.schema';

interface Props {
  items: OSPorStatusItemData[];
  totalAtivas: number;
  isLoading: boolean;
  isError: boolean;
}

defineProps<Props>();

const statusConfig: Record<string, { dot: string; badge: string }> = {
  ABERTA:               { dot: 'bg-blue-400',   badge: 'bg-blue-50 text-blue-700 border-blue-200' },
  EM_ANDAMENTO:         { dot: 'bg-yellow-400',  badge: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
  AGUARDANDO_PECAS:     { dot: 'bg-orange-400',  badge: 'bg-orange-50 text-orange-700 border-orange-200' },
  AGUARDANDO_APROVACAO: { dot: 'bg-purple-400',  badge: 'bg-purple-50 text-purple-700 border-purple-200' },
  AGUARDANDO_RETIRADA:  { dot: 'bg-teal-400',    badge: 'bg-teal-50 text-teal-700 border-teal-200' },
};
</script>

<template>
  <div class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-hidden flex flex-col">
    <div class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-2">
      <LayoutGrid :size="18" class="text-zinc-500" />
      <h3 class="font-bold text-base md:text-lg text-zinc-900">OS por Status</h3>
      <span v-if="totalAtivas > 0" class="ml-auto text-xs font-semibold bg-zinc-100 text-zinc-500 px-2 py-0.5 rounded-full">
        {{ totalAtivas }} ativas
      </span>
    </div>

    <div v-if="isError" class="p-8 text-center text-red-500 text-sm flex-1 flex items-center justify-center">
      Erro ao carregar dados
    </div>

    <div v-else-if="isLoading" class="p-6 space-y-3 flex-1">
      <div v-for="i in 5" :key="i" class="h-10 bg-zinc-100 rounded-lg animate-pulse" />
    </div>

    <div v-else-if="items.length > 0" class="p-4 md:p-6 space-y-3 flex-1">
      <div
        v-for="item in items"
        :key="item.status"
        class="flex items-center gap-3"
      >
        <span :class="['w-2.5 h-2.5 rounded-full shrink-0', statusConfig[item.status]?.dot ?? 'bg-zinc-400']" />
        <span class="text-sm text-zinc-700 flex-1">{{ item.status_label }}</span>
        <span :class="['px-2.5 py-0.5 rounded-full text-xs font-bold border', statusConfig[item.status]?.badge ?? 'bg-zinc-50 text-zinc-600 border-zinc-200']">
          {{ item.count }}
        </span>
      </div>
    </div>

    <div v-else class="p-8 text-center text-zinc-400 text-sm flex-1 flex items-center justify-center">
      Nenhuma OS ativa
    </div>
  </div>
</template>
