<script setup lang="ts">
/**
 * @component EditorAvisos
 * @description Avisos do motor em frases (Spec 06B D17, §6.6). O texto
 * depende de quem vê: sem custos, a margem negativa aparece sem números.
 * Código desconhecido (de uma spec futura) simplesmente não aparece.
 */
import { computed } from 'vue';
import { AlertTriangle, Info } from 'lucide-vue-next';

import { textosDosAvisos } from '../../constants/avisos.constants';

const props = defineProps<{
  codigos: string[];
  incluiCustos: boolean;
  /** Faixa "os preços podem ter mudado" para quem não vê custos (D39). */
  avisoPrecos?: boolean;
}>();

const avisos = computed(() => textosDosAvisos(props.codigos, props.incluiCustos));
</script>

<template>
  <div v-if="avisos.length || avisoPrecos" class="flex flex-col gap-2" data-testid="avisos">
    <p
      v-for="aviso in avisos"
      :key="aviso.codigo"
      class="flex items-start gap-2 rounded-xl border px-4 py-2.5 text-sm"
      :class="aviso.tom === 'atencao' ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-zinc-200 bg-zinc-50 text-zinc-600'"
      :data-testid="`aviso-${aviso.codigo}`"
    >
      <AlertTriangle v-if="aviso.tom === 'atencao'" :size="16" class="mt-0.5 shrink-0" />
      <Info v-else :size="16" class="mt-0.5 shrink-0" />
      {{ aviso.texto }}
    </p>
    <p v-if="avisoPrecos" class="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-900" data-testid="aviso-precos">
      <AlertTriangle :size="16" class="mt-0.5 shrink-0" />
      Os preços dos insumos podem ter mudado. Peça a quem vê os custos para conferir antes de enviar.
    </p>
  </div>
</template>
