<script setup lang="ts">
import { Printer, FileText, Receipt } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

interface Props {
  isOpen: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  close: [];
  select: [format: 'A4' | 'CUPOM'];
}>();
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Formato de Impressão"
    subtitle="Selecione o formato desejado para imprimir esta OS."
    size="sm"
    @close="emit('close')"
  >
    <template #header>
      <div class="flex flex-col items-center text-center p-6 border-b border-zinc-100">
        <div class="bg-brand-primary-light w-16 h-16 rounded-full flex items-center justify-center mb-4">
          <Printer :size="32" class="text-brand-primary" />
        </div>
        <h2 class="text-lg font-bold text-zinc-900">Formato de Impressão</h2>
        <p class="text-sm text-zinc-500 mt-0.5 max-w-xs mx-auto">
          Selecione o formato desejado para imprimir esta OS.
        </p>
      </div>
    </template>

    <div class="space-y-3">
      <button
        type="button"
        class="w-full flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-brand-primary hover:bg-brand-primary-light hover:shadow-md transition-all group text-left"
        @click="emit('select', 'A4')"
      >
        <div class="flex items-center gap-3">
          <div class="bg-white p-2 rounded-lg border border-slate-100 group-hover:border-brand-primary/20 text-slate-400 group-hover:text-brand-primary transition-colors">
            <FileText :size="20" />
          </div>
          <div>
            <p class="font-bold text-slate-700 group-hover:text-brand-primary">Folha A4</p>
            <p class="text-xs text-slate-500">Impressão padrão em folha A4 com layout completo</p>
          </div>
        </div>
        <div class="w-4 h-4 rounded-full border border-slate-300 group-hover:border-brand-primary group-hover:bg-brand-primary transition-colors"></div>
      </button>

      <button
        type="button"
        class="w-full flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-brand-primary hover:bg-brand-primary-light hover:shadow-md transition-all group text-left"
        @click="emit('select', 'CUPOM')"
      >
        <div class="flex items-center gap-3">
          <div class="bg-white p-2 rounded-lg border border-slate-100 group-hover:border-brand-primary/20 text-slate-400 group-hover:text-brand-primary transition-colors">
            <Receipt :size="20" />
          </div>
          <div>
            <p class="font-bold text-slate-700 group-hover:text-brand-primary">Cupom Térmico</p>
            <p class="text-xs text-slate-500">Impressão em bobina térmica 80mm (cupom não fiscal)</p>
          </div>
        </div>
        <div class="w-4 h-4 rounded-full border border-slate-300 group-hover:border-brand-primary group-hover:bg-brand-primary transition-colors"></div>
      </button>
    </div>

    <template #footer>
      <div class="flex justify-center w-full">
        <BaseButton variant="ghost" class="text-slate-400 hover:text-slate-600 px-6 py-2" @click="emit('close')">
          Cancelar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
