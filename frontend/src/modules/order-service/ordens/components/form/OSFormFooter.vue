<script setup lang="ts">
import { computed } from 'vue';
import { CheckCircle2, Printer, FileText, Unlock } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  valorTotal: number;
  isFinalizada: boolean;
  isCancelada?: boolean;
  isEditMode: boolean;
  isCreateMode: boolean;
  isPending: boolean;
  reopenMode: 'NONE' | 'TEXT_ONLY' | 'FULL';
  osId?: number;
}

const isLocked = computed(() => props.isFinalizada || props.isCancelada);

const props = defineProps<Props>();

const emit = defineEmits<{
  finalizar: [];
  print: [];
  reprintExit: [];
  reopen: [];
  save: [];
}>();

const saveIcon = computed(() => {
  return props.reopenMode === 'TEXT_ONLY' ? FileText : CheckCircle2;
});

const saveLabel = computed(() => {
  if (props.isCreateMode) return 'CRIAR O.S.';
  if (props.reopenMode === 'TEXT_ONLY') return 'SALVAR TEXTO';
  return 'SALVAR';
});
</script>

<template>
  <div class="flex flex-col md:flex-row justify-between items-center gap-4">
    <div class="flex items-center gap-3">
      <span class="text-xs font-bold text-zinc-500 uppercase">Total O.S.</span>
      <span class="text-xl font-bold text-zinc-800">{{ formatCurrency(valorTotal) }}</span>
    </div>

    <div class="flex items-center gap-2">
      <!-- Impressao -->
      <BaseButton
        v-if="isEditMode"
        variant="secondary"
        size="sm"
        :disabled="!osId"
        @click="emit('print')"
      >
        <Printer :size="16" class="mr-1" />
        ENTRADA
      </BaseButton>

      <BaseButton
        v-if="isEditMode && isFinalizada"
        variant="secondary"
        size="sm"
        @click="emit('reprintExit')"
      >
        <Printer :size="16" class="mr-1" />
        SAÍDA
      </BaseButton>

      <!-- Reabrir (OS finalizada ou cancelada) -->
      <BaseButton
        v-if="isEditMode && isLocked && reopenMode === 'NONE'"
        variant="secondary"
        @click="emit('reopen')"
      >
        <Unlock :size="16" class="mr-1" />
        REABRIR
      </BaseButton>

      <!-- Finalizar (só edit mode, não locked, não TEXT_ONLY) -->
      <BaseButton
        v-if="isEditMode && !isLocked && reopenMode !== 'TEXT_ONLY'"
        variant="primary"
        @click="emit('finalizar')"
      >
        <CheckCircle2 :size="16" class="mr-1" />
        FINALIZAR
      </BaseButton>

      <!-- Salvar (criar ou editar, não locked sem reopen) -->
      <BaseButton
        v-if="!isLocked || reopenMode !== 'NONE'"
        variant="primary"
        :is-loading="isPending"
        @click="emit('save')"
      >
        <component :is="saveIcon" :size="16" class="mr-1" />
        {{ saveLabel }}
      </BaseButton>
    </div>
  </div>
</template>
