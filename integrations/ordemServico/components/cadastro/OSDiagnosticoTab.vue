<script setup lang="ts">
/**
 * OSDiagnosticoTab.vue
 * Aba de diagnostico tecnico e galeria de fotos
 */
import { ClipboardList } from 'lucide-vue-next';
import OSFotoGallery from './OSFotoGallery.vue';
import type { OrdemServicoFotoRead } from '../../types/ordemServico.types';

interface Props {
  diagnostico: string;
  osId?: number;
  fotos: OrdemServicoFotoRead[];
  isLocked: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:diagnostico': [value: string];
  photoChange: [];
}>();

function handleDiagnosticoInput(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  emit('update:diagnostico', target.value);
}
</script>

<template>
  <div class="space-y-4 animate-fadeIn">
    <!-- Info Box -->
    <div class="bg-brand-primary-light border-l-4 border-brand-primary-light0 p-4 rounded-r-xl mb-4">
      <h5 class="text-sm font-bold text-brand-primary flex items-center gap-2">
        <ClipboardList :size="16" /> Area Tecnica
      </h5>
      <p class="text-xs text-brand-primary mt-1">
        Espaco reservado para o laudo tecnico.
      </p>
    </div>

    <!-- Textarea Diagnostico -->
    <div>
      <label class="block text-sm font-bold text-slate-700 mb-2">
        Laudo Tecnico / Diagnostico
      </label>
      <textarea
        :value="diagnostico"
        rows="12"
        class="w-full rounded-xl border border-slate-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary font-mono text-sm leading-relaxed p-4"
        placeholder="Descreva os testes realizados, componentes analisados e o diagnostico final..."
        :disabled="isLocked"
        @input="handleDiagnosticoInput"
      ></textarea>
    </div>

    <!-- Galeria de Fotos -->
    <div class="pt-4 border-t border-slate-200">
      <OSFotoGallery
        v-if="osId"
        :ordem-servico-id="osId"
        :fotos="fotos"
        :read-only="isLocked"
        @uploaded="emit('photoChange')"
        @deleted="emit('photoChange')"
      />
      <div
        v-else
        class="text-center py-4 bg-slate-50 border border-dashed border-slate-200 rounded-lg text-slate-500 text-sm"
      >
        Salve a OS antes de adicionar fotos.
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
