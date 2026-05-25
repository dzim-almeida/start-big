<script setup lang="ts">
import { ChevronRight, X } from 'lucide-vue-next';
import type { QuickActionItem } from '@/modules/home/types/dashboard.types';

interface Props {
  actions: QuickActionItem[];
}

defineProps<Props>();

const emit = defineEmits<{
  clicked: [];
}>();

function handleAction(action: QuickActionItem) {
  emit('clicked');
  action.action();
}
</script>

<template>
  <div class="bg-brand-action rounded-2xl md:rounded-3xl p-4 md:p-6 text-white shadow-xl">
    <div class="flex justify-between items-center">
      <h3 class="font-bold text-base md:text-lg mb-4 md:mb-6">Acesso Rápido</h3>
      <X :size="20" class="mb-4 md:mb-6 cursor-pointer" @click="emit('clicked')" />
    </div>

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
        @click="handleAction(action)"
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

    <div class="mt-5">
      <div className="relative z-10 text-center">
        <p className="text-xs text-slate-300">
          Use
          <code className="bg-zinc-800 px-1 py-0.5 rounded text-white border border-zinc-400"
            >Ctrl + K</code
          >
          para abrir este menu.
        </p>
      </div>
    </div>
  </div>
</template>
