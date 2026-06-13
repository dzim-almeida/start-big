<script setup lang="ts">
import { X, Keyboard } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import { SALE_SHORTCUTS, type ShortcutItem } from '../../constants';

withDefaults(defineProps<{
  isOpen: boolean;
  shortcuts?: ShortcutItem[];
}>(), {
  shortcuts: () => SALE_SHORTCUTS,
});

const emit = defineEmits<{
  (e: 'close'): void;
}>();
</script>

<template>
  <BaseModal :is-open="isOpen" title="Atalhos do Teclado" size="sm" @close="emit('close')">
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-primary/10 text-brand-primary">
            <Keyboard :size="18" />
          </div>
          <h2 class="text-lg font-bold text-zinc-800">Atalhos do Teclado</h2>
        </div>
        <button
          type="button"
          class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          @click="emit('close')"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <div class="flex flex-col gap-1 p-2">
      <div
        v-for="shortcut in shortcuts"
        :key="shortcut.keys"
        class="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-zinc-50 transition-colors"
      >
        <span class="text-sm text-zinc-600">{{ shortcut.description }}</span>
        <div class="flex items-center gap-1">
          <kbd
            v-for="key in shortcut.keys.split('+')"
            :key="key"
            class="inline-flex h-6 min-w-6 items-center justify-center rounded-md border border-zinc-300 bg-zinc-100 px-1.5 text-[11px] font-semibold text-zinc-600 shadow-sm"
          >
            {{ key }}
          </kbd>
        </div>
      </div>
    </div>
  </BaseModal>
</template>
