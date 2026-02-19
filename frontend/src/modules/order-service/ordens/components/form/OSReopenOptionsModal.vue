<script setup lang="ts">
import { FileText, Unlock } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

interface Props {
  isOpen: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  cancel: [];
  textOnly: [];
  full: [];
}>();
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Reabrir Ordem de Serviço"
    subtitle="Como deseja reabrir esta OS? Escolha o nível de edição necessário."
    size="md"
    @close="emit('cancel')"
  >
    <template #header>
      <div class="flex flex-col items-center text-center p-6 border-b border-zinc-100">
        <div class="bg-brand-primary-light w-16 h-16 rounded-full flex items-center justify-center mb-4">
          <Unlock :size="32" class="text-brand-primary" />
        </div>
        <h2 class="text-lg font-bold text-zinc-900">Reabrir Ordem de Serviço</h2>
        <p class="text-sm text-zinc-500 mt-0.5 max-w-xs mx-auto">
          Como deseja reabrir esta OS? Escolha o nível de edição necessário.
        </p>
      </div>
    </template>

    <div class="space-y-3">
      <button
        type="button"
        class="w-full flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-brand-primary hover:bg-brand-primary-light hover:shadow-md transition-all group text-left"
        @click="emit('textOnly')"
      >
        <div class="flex items-center gap-3">
          <div class="bg-white p-2 rounded-lg border border-slate-100 group-hover:border-brand-primary/20 text-slate-400 group-hover:text-brand-primary transition-colors">
            <FileText :size="20" />
          </div>
          <div>
            <p class="font-bold text-slate-700 group-hover:text-brand-primary">Ajustar Apenas Texto</p>
            <p class="text-xs text-slate-500">Edite diagnóstico, descrição e observações. Mantém financeiro travado.</p>
          </div>
        </div>
        <div class="w-4 h-4 rounded-full border border-slate-300 group-hover:border-brand-primary group-hover:bg-brand-primary transition-colors"></div>
      </button>

      <button
        type="button"
        class="w-full flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-brand-primary hover:bg-brand-primary-light hover:shadow-md transition-all group text-left"
        @click="emit('full')"
      >
        <div class="flex items-center gap-3">
          <div class="bg-white p-2 rounded-lg border border-slate-100 group-hover:border-brand-primary/20 text-slate-400 group-hover:text-brand-primary transition-colors">
            <Unlock :size="20" />
          </div>
          <div>
            <p class="font-bold text-slate-700 group-hover:text-brand-primary">Reabertura Completa</p>
            <p class="text-xs text-slate-500">Libera edição de itens, valores e pagamentos. Requer nova finalização.</p>
          </div>
        </div>
        <div class="w-4 h-4 rounded-full border border-slate-300 group-hover:border-brand-primary group-hover:bg-brand-primary transition-colors"></div>
      </button>
    </div>

    <template #footer>
      <div class="flex justify-center w-full">
        <BaseButton variant="ghost" class="text-slate-400 hover:text-slate-600 px-6 py-2" @click="emit('cancel')">
          Cancelar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
