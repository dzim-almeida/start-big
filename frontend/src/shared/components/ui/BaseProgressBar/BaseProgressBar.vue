<script setup lang="ts">
import { computed } from 'vue';

/**
 * Barra de progresso com `role="progressbar"`: o leitor de tela anuncia o
 * percentual, e o rótulo (opcional) aparece em cima, à esquerda, com o valor
 * à direita — o formato do "Progresso do ambiente" e da separação.
 */
const props = withDefaults(
  defineProps<{
    /** 0 a 100; fora disso é cortado. */
    valor: number;
    rotulo?: string;
    /** Texto do lado direito; sem ele, mostra "NN%". */
    detalhe?: string;
    /** `sucesso` pinta de verde (ex.: 100%); o padrão é a cor da marca. */
    tom?: 'primario' | 'sucesso';
  }>(),
  { tom: 'primario' },
);

const pct = computed(() => Math.min(100, Math.max(0, Math.round(props.valor))));
const textoDireita = computed(() => props.detalhe ?? `${pct.value}%`);
</script>

<template>
  <div class="w-full">
    <div v-if="rotulo || detalhe" class="mb-1.5 flex items-baseline justify-between gap-3">
      <span v-if="rotulo" class="text-xs font-semibold uppercase tracking-wider text-zinc-500">{{ rotulo }}</span>
      <span class="text-sm font-bold tabular-nums text-brand-primary">{{ textoDireita }}</span>
    </div>
    <div
      class="h-2 w-full overflow-hidden rounded-full bg-zinc-200"
      role="progressbar"
      :aria-valuenow="pct"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="rotulo"
    >
      <div
        :class="['h-full rounded-full transition-all', tom === 'sucesso' ? 'bg-emerald-600' : 'bg-brand-primary']"
        :style="{ width: `${pct}%` }"
      />
    </div>
  </div>
</template>
