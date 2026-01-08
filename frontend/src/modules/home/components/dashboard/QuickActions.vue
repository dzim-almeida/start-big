<script setup lang="ts">
import { Package, ChevronRight } from 'lucide-vue-next';
import type { QuickActionItem } from '../../types/dashboard.types';

interface Props {
  actions: QuickActionItem[];
  lowStockCount: number;
}

defineProps<Props>();
</script>

<template>
  <div class="bg-brand-action rounded-2xl md:rounded-3xl p-4 md:p-6 text-white shadow-xl">
    <h3 class="font-bold text-base md:text-lg mb-4 md:mb-6">Acesso Rápido</h3>

    <!-- Quick Action Buttons -->
    <div class="space-y-3 md:space-y-4">
      <button
        v-for="action in actions"
        :key="action.id"
        :class="[
          'w-full flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl md:rounded-2xl transition-all duration-200 group',
          action.variant === 'primary'
            ? 'bg-brand-primary hover:bg-brand-primary/90'
            : 'bg-zinc-800 hover:bg-zinc-700',
        ]"
      >
        <div
          class="w-9 h-9 md:w-10 md:h-10 rounded-lg md:rounded-xl bg-white/10 flex items-center justify-center group-hover:scale-110 transition-transform"
        >
          <component :is="action.icon" :size="18" class="text-white md:w-5 md:h-5" />
        </div>
        <span class="text-sm font-bold">{{ action.label }}</span>
        <ChevronRight
          :size="16"
          class="ml-auto opacity-30 group-hover:opacity-100 group-hover:translate-x-1 transition-all"
        />
      </button>
    </div>

    <!-- Low Stock Alert -->
    <div
      v-if="lowStockCount > 0"
      class="mt-6 md:mt-8 p-4 bg-gradient-to-br from-brand-primary to-indigo-700 rounded-xl md:rounded-2xl relative overflow-hidden group cursor-pointer hover:shadow-lg transition-shadow"
    >
      <div class="relative z-10">
        <p class="text-[10px] md:text-xs font-bold text-blue-100/80 uppercase tracking-wide">
          Aviso de Estoque
        </p>
        <p class="text-sm md:text-base font-bold mt-1">
          {{ lowStockCount }} {{ lowStockCount === 1 ? 'Item está' : 'Itens estão' }} acabando!
        </p>
        <button
          class="mt-3 md:mt-4 bg-white text-brand-primary px-3 md:px-4 py-1.5 md:py-2 rounded-lg text-[11px] md:text-xs font-bold flex items-center gap-1.5 md:gap-2 transition-all hover:bg-zinc-100 active:scale-95"
        >
          <span>Reabastecer</span>
          <ChevronRight :size="14" />
        </button>
      </div>

      <!-- Background Icon -->
      <div
        class="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-110 group-hover:opacity-15 transition-all duration-300"
      >
        <Package :size="120" />
      </div>
    </div>
  </div>
</template>
