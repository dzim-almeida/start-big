<script setup lang="ts">
import { ClipboardList } from 'lucide-vue-next';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import OSFotoGallery from './OSFotoGallery.vue';
import type { OrdemServicoFotoRead } from '../../types/ordemServico.types';

interface Props {
  diagnostico: string;
  osId?: number;
  fotos: OrdemServicoFotoRead[];
  isLocked: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  'update:diagnostico': [value: string];
  photoChange: [];
}>();
</script>

<template>
  <div class="space-y-4 animate-fadeIn">
    <div class="bg-brand-primary-light border-l-4 border-brand-primary p-4 rounded-r-xl mb-4">
      <h5 class="text-sm font-bold text-brand-primary flex items-center gap-2">
        <ClipboardList :size="16" /> Area Tecnica
      </h5>
      <p class="text-xs text-brand-primary mt-1">
        Espaco reservado para o laudo tecnico.
      </p>
    </div>

    <div>
      <BaseTextarea
        :model-value="diagnostico"
        label="Laudo Tecnico / Diagnostico"
        :rows="12"
        placeholder="Descreva os testes realizados, componentes analisados e o diagnostico final..."
        :disabled="isLocked"
        @update:model-value="emit('update:diagnostico', $event as string)"
      />
    </div>

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
