<script setup lang="ts">
import { computed } from 'vue';
import { CheckCircle2, Printer, FileText, Unlock } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

interface Props {
  isFinalizada: boolean;
  isCancelada?: boolean;
  isEditMode: boolean;
  isCreateMode: boolean;
  isPending: boolean;
  reopenMode: 'NONE' | 'TEXT_ONLY' | 'FULL';
  osId?: number;
  /** Só segmentos com vistoria (ex.: oficina) exibem o botão de ficha. */
  showFicha?: boolean;
}

const isLocked = computed(() => props.isFinalizada || props.isCancelada);

const props = defineProps<Props>();

const emit = defineEmits<{
  finalizar: [];
  print: [];
  reprintExit: [];
  reopen: [];
  save: [];
  printFicha: [tipo: 'ENTRADA' | 'SAIDA'];
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
  <div class="flex flex-col md:flex-row items-center gap-4">

    <div class="flex items-center ml-auto gap-2">
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
        size="sm"
        @click="emit('reopen')"
      >
        <Unlock :size="16" class="mr-1" />
        REABRIR
      </BaseButton>

      <!-- Finalizar (só edit mode, não locked, não TEXT_ONLY) -->
      <BaseButton
        v-if="isEditMode && !isLocked && reopenMode !== 'TEXT_ONLY'"
        variant="primary"
        size="sm"
        @click="emit('finalizar')"
      >
        <CheckCircle2 :size="16" class="mr-1" />
        FINALIZAR
      </BaseButton>

      <!-- Ficha de vistoria de ENTRADA (em branco) — só segmentos com vistoria.
           Disponível já na criação, para imprimir antes de salvar a OS. -->
      <BaseButton
        v-if="showFicha && (!isLocked || reopenMode !== 'NONE')"
        variant="secondary"
        size="sm"
        type="button"
        @click="emit('printFicha', 'ENTRADA')"
      >
        <Printer :size="16" class="mr-1" />
        FICHA
      </BaseButton>

      <!-- Salvar (criar ou editar, não locked sem reopen) -->
      <BaseButton
        v-if="!isLocked || reopenMode !== 'NONE'"
        variant="primary"
        size="sm"
        :is-loading="isPending"
        @click="emit('save')"
      >
        <component :is="saveIcon" :size="16" class="mr-1" />
        {{ saveLabel }}
      </BaseButton>
    </div>
  </div>
</template>
