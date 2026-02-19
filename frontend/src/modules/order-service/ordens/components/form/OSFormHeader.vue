<script setup lang="ts">
import { computed } from 'vue';
import { CheckCircle2, Printer, FileText, Unlock } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

interface Props {
  osNumber: string | number;
  osId?: number;
  isFinalizada: boolean;
  isPending: boolean;
  reopenMode: 'NONE' | 'TEXT_ONLY' | 'FULL';
}

const props = defineProps<Props>();

const emit = defineEmits<{
  print: [];
  reprintExit: [];
  reopen: [];
  save: [];
  close: [];
}>();

const displayNumber = computed(() => {
  const num = String(props.osNumber);
  return num.replace(/^OS-\d{4}-/, '') || '...';
});

const saveIcon = computed(() => {
  return props.reopenMode === 'TEXT_ONLY' ? FileText : CheckCircle2;
});
</script>

<template>
  <div class="bg-slate-900 text-white p-5 rounded-t-2xl">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-slate-400 text-sm font-bold">O.S.nº</span>
        <span class="text-3xl font-black tracking-widest text-white">{{ displayNumber }}</span>
      </div>

      <div class="flex items-center gap-3">
        <BaseButton variant="secondary" :disabled="!osId" @click="emit('print')">
          <Printer :size="16" class="mr-2" />
          ENTRADA
        </BaseButton>

        <BaseButton v-if="isFinalizada" variant="secondary" @click="emit('reprintExit')">
          <Printer :size="16" class="mr-2" />
          SAÍDA
        </BaseButton>

        <BaseButton v-if="isFinalizada" variant="primary" @click="emit('reopen')">
          <Unlock :size="16" class="mr-2" />
          REABRIR OS
        </BaseButton>

        <BaseButton v-if="!isFinalizada" variant="primary" :is-loading="isPending" @click="emit('save')">
          <component :is="saveIcon" :size="16" class="mr-2" />
          SALVAR
        </BaseButton>

        <BaseButton variant="slate" @click="emit('close')">
          FECHAR
        </BaseButton>
      </div>
    </div>
  </div>
</template>
