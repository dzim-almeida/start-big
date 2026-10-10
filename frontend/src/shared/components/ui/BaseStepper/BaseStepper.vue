<script setup lang="ts">
import { computed } from 'vue';
import { Check } from 'lucide-vue-next';

/**
 * Linha de etapas (concluída → atual → pendente), na horizontal. Os círculos
 * levam o número; a etapa concluída troca o número por um check e a atual
 * ganha um halo. O estado também vai no texto (`aria-current="step"`), não só
 * na cor.
 */
export interface EtapaStepper {
  rotulo: string;
  estado: 'concluida' | 'atual' | 'pendente';
}

const props = defineProps<{ etapas: EtapaStepper[] }>();

/** Quanto da linha de fundo pinta de verde: até a última etapa concluída. */
const preenchido = computed(() => {
  const n = props.etapas.length;
  if (n < 2) return 0;
  const ultimaConcluida = props.etapas.map((e) => e.estado).lastIndexOf('concluida');
  return ultimaConcluida < 0 ? 0 : (Math.min(ultimaConcluida + 1, n - 1) / (n - 1)) * 100;
});
</script>

<template>
  <ol class="relative flex" aria-label="Etapas">
    <!-- Linha atrás dos círculos: do centro do primeiro ao centro do último. -->
    <div
      class="pointer-events-none absolute top-4 h-0.5 bg-zinc-200"
      :style="{ left: `${50 / etapas.length}%`, right: `${50 / etapas.length}%` }"
      aria-hidden="true"
    >
      <div class="h-full bg-emerald-600 transition-all" :style="{ width: `${preenchido}%` }" />
    </div>

    <li
      v-for="(etapa, i) in etapas"
      :key="etapa.rotulo"
      class="relative z-10 flex flex-1 flex-col items-center gap-1.5 text-center"
      :aria-current="etapa.estado === 'atual' ? 'step' : undefined"
    >
      <span
        :class="[
          'flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold',
          etapa.estado === 'concluida' && 'border-emerald-600 bg-emerald-600 text-white',
          etapa.estado === 'atual' && 'border-brand-primary bg-brand-primary text-white ring-4 ring-brand-primary-light',
          etapa.estado === 'pendente' && 'border-zinc-300 bg-white text-zinc-500',
        ]"
      >
        <Check v-if="etapa.estado === 'concluida'" :size="16" aria-hidden="true" />
        <template v-else>{{ i + 1 }}</template>
      </span>
      <span
        :class="[
          'max-w-32 text-xs',
          etapa.estado === 'concluida' && 'font-semibold text-emerald-700',
          etapa.estado === 'atual' && 'font-semibold text-brand-primary',
          etapa.estado === 'pendente' && 'text-zinc-500',
        ]"
      >
        {{ etapa.rotulo }}
      </span>
    </li>
  </ol>
</template>
