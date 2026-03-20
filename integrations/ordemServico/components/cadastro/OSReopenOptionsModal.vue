<script setup lang="ts">
/**
 * OSReopenOptionsModal.vue
 * Modal overlay para escolher modo de reabertura da OS
 */
import { FileText, Unlock } from 'lucide-vue-next';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';

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
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn"
    >
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100 p-6 space-y-6">
        <!-- Header -->
        <div class="space-y-2 text-center">
          <div class="bg-brand-primary-light w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Unlock :size="32" class="text-brand-primary" />
          </div>
          <h3 class="text-xl font-bold text-slate-800">Reabrir Ordem de Serviço</h3>
          <p class="text-sm text-slate-500 max-w-xs mx-auto">
            Como deseja reabrir esta OS? Escolha o nível de edição necessário.
          </p>
        </div>

        <!-- Options -->
        <div class="space-y-3">
          <!-- Text Only Option -->
          <button
            type="button"
            class="w-full flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-brand-primary-light0 hover:bg-brand-primary-light hover:shadow-md transition-all group text-left"
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
            <div class="w-4 h-4 rounded-full border border-slate-300 group-hover:border-brand-primary-light0 group-hover:bg-brand-primary-light0 transition-colors"></div>
          </button>

          <!-- Full Reopen Option -->
          <button
            type="button"
            class="w-full flex items-center justify-between p-4 rounded-xl border border-slate-200 hover:border-brand-primary-light0 hover:bg-brand-primary-light hover:shadow-md transition-all group text-left"
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
            <div class="w-4 h-4 rounded-full border border-slate-300 group-hover:border-brand-primary-light0 group-hover:bg-brand-primary-light0 transition-colors"></div>
          </button>
        </div>

        <!-- Footer -->
        <div class="pt-2 border-t border-slate-100 flex justify-center">
          <BaseButton
            variant="ghost"
            class="text-slate-400 hover:text-slate-600 px-6 py-2"
            @click="emit('cancel')"
          >
            Cancelar
          </BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
