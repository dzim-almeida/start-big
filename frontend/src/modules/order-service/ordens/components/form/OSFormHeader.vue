<script setup lang="ts">
import { computed } from 'vue';
import { X } from 'lucide-vue-next';

interface Props {
  osNumber: string | number;
  isFinalizada: boolean;
  isCancelada?: boolean;
  isCreateMode: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
}>();

const displayNumber = computed(() => {
  const num = String(props.osNumber);
  return num.replace(/^OS-\d{4}-/, '') || '...';
});

const headerTitle = computed(() => {
  if (props.isCreateMode) return 'Nova Ordem de Serviço';
  return `O.S. #${displayNumber.value}`;
});
</script>

<template>
  <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
    <div class="flex items-center gap-3">
      <h2 class="text-xl font-bold text-zinc-800">{{ headerTitle }}</h2>
      <span
        v-if="!isCreateMode && isFinalizada"
        class="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700"
      >
        FINALIZADA
      </span>
      <span
        v-if="!isCreateMode && isCancelada"
        class="px-2 py-0.5 text-xs font-medium rounded-full bg-red-50 text-red-700"
      >
        CANCELADA
      </span>
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
