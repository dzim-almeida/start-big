<script setup lang="ts">
import { ref } from 'vue';
import { FileText, Receipt } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import type { PrintFormat } from './print.types';

interface Props {
  isOpen: boolean;
  subtitle?: string;
}

withDefaults(defineProps<Props>(), {
  subtitle: 'Selecione o formato desejado para impressão.',
});

const emit = defineEmits<{
  close: [];
  select: [format: PrintFormat];
}>();

const selecionado = ref<PrintFormat>('A4');
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Formato de Impressão"
    size="sm"
    @close="emit('close')"
  >
    <div class="flex gap-3">
      <button
        type="button"
        :class="[
          'flex-1 flex flex-col items-center gap-2 py-3 px-2 rounded-xl border-2 transition-all cursor-pointer',
          selecionado === 'A4'
            ? 'border-brand-primary bg-brand-primary-light text-brand-primary'
            : 'border-zinc-200 bg-white text-zinc-500 hover:border-brand-primary hover:text-brand-primary',
        ]"
        @click="selecionado = 'A4'"
      >
        <FileText :size="20" />
        <span class="text-xs font-semibold">Folha A4</span>
      </button>

      <button
        type="button"
        :class="[
          'flex-1 flex flex-col items-center gap-2 py-3 px-2 rounded-xl border-2 transition-all cursor-pointer',
          selecionado === 'CUPOM'
            ? 'border-brand-primary bg-brand-primary-light text-brand-primary'
            : 'border-zinc-200 bg-white text-zinc-500 hover:border-brand-primary hover:text-brand-primary',
        ]"
        @click="selecionado = 'CUPOM'"
      >
        <Receipt :size="20" />
        <span class="text-xs font-semibold">Cupom Térmico</span>
      </button>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <BaseButton variant="secondary" class="px-5" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton variant="primary" class="px-5" @click="emit('select', selecionado)">
          Imprimir
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
