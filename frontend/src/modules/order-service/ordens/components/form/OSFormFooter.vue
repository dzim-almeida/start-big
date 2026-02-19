<script setup lang="ts">
import { CheckCircle2 } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  valorTotal: number;
  isFinalizada: boolean;
  isEditMode: boolean;
  reopenMode: 'NONE' | 'TEXT_ONLY' | 'FULL';
}

defineProps<Props>();

const emit = defineEmits<{
  finalizar: [];
}>();
</script>

<template>
  <div class="flex flex-col md:flex-row justify-between items-center gap-4">
    <div class="flex items-center gap-3">
      <span class="text-xs font-bold text-slate-500 uppercase">Total O.S.</span>
      <span class="text-2xl font-black text-slate-800">{{ formatCurrency(valorTotal) }}</span>
    </div>

    <div class="flex items-center gap-2">
      <template v-if="isFinalizada">
        <!-- Acoes movidas para o header -->
      </template>

      <template v-else>
        <BaseButton
          v-if="isEditMode && reopenMode !== 'TEXT_ONLY'"
          variant="primary"
          @click="emit('finalizar')"
        >
          <CheckCircle2 :size="16" class="mr-2" />
          FINALIZAR
        </BaseButton>
      </template>
    </div>
  </div>
</template>
