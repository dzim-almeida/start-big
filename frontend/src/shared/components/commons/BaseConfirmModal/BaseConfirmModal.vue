<script setup lang="ts">
import { Power } from 'lucide-vue-next';

interface Props {
  isOpen: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  icon?: any;
}

withDefaults(defineProps<Props>(), {
  description: '',
  confirmLabel: 'Confirmar',
  cancelLabel: 'Cancelar',
  variant: 'warning',
});

const emit = defineEmits<{
  close: [];
  confirm: [];
}>();
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-900/60 backdrop-blur-sm">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden border border-zinc-100">
      <div class="p-6 text-center">
        <!-- Icone Genérico (sempre Power por enquanto para manter visual idêntico, 
             mas poderia ser dinâmico no futuro se necessário) -->
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full mb-4 bg-blue-50 text-blue-500">
          <component :is="icon || Power" :size="24" />
        </div>

        <h3 class="text-lg font-bold text-zinc-900">
          {{ title }}
        </h3>
        
        <div class="text-sm text-zinc-500 mt-2">
          <slot name="description">
            {{ description }}
          </slot>
        </div>
      </div>

      <div class="bg-zinc-50 p-4 flex gap-3 border-t border-zinc-100">
        <button
          type="button"
          class="flex-1 px-4 py-2 text-sm font-medium text-zinc-600 bg-white border border-zinc-200 rounded-xl hover:bg-zinc-100 transition-colors"
          @click="emit('close')"
        >
          {{ cancelLabel }}
        </button>
        <button
          type="button"
          class="flex-1 px-4 py-2 text-sm font-medium text-white bg-brand-primary rounded-xl hover:opacity-90 shadow-md transition-all"
          @click="emit('confirm')"
        >
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>
