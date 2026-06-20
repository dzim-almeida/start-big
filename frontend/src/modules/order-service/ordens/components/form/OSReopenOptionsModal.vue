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
    title="Reabrir OS"
    subtitle="Escolha o nível de edição necessário."
    size="sm"
    @close="emit('cancel')"
  >
    <div class="flex flex-col gap-2">
      <button
        type="button"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl border-2 border-zinc-200 hover:border-brand-primary hover:bg-brand-primary-light transition-all text-left group cursor-pointer"
        @click="emit('textOnly')"
      >
        <div class="p-2 rounded-lg bg-zinc-100 group-hover:bg-brand-primary/10 shrink-0 transition-colors">
          <FileText :size="16" class="text-zinc-500 group-hover:text-brand-primary transition-colors" />
        </div>
        <div>
          <p class="text-sm font-semibold text-zinc-700 group-hover:text-brand-primary transition-colors">Ajustar Apenas Texto</p>
          <p class="text-xs text-zinc-400 leading-tight">Edite diagnóstico e observações. Financeiro travado.</p>
        </div>
      </button>

      <button
        type="button"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl border-2 border-zinc-200 hover:border-amber-400 hover:bg-amber-50 transition-all text-left group cursor-pointer"
        @click="emit('full')"
      >
        <div class="p-2 rounded-lg bg-zinc-100 group-hover:bg-amber-100 shrink-0 transition-colors">
          <Unlock :size="16" class="text-zinc-500 group-hover:text-amber-600 transition-colors" />
        </div>
        <div>
          <p class="text-sm font-semibold text-zinc-700 group-hover:text-amber-700 transition-colors">Reabertura Completa</p>
          <p class="text-xs text-zinc-400 leading-tight">Libera itens, valores e pagamentos. Requer nova finalização.</p>
        </div>
      </button>
    </div>

    <template #footer>
      <div class="flex justify-end w-full">
        <BaseButton variant="secondary" class="px-5" @click="emit('cancel')">
          Cancelar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
