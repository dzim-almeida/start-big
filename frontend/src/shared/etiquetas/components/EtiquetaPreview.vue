<script setup lang="ts">
/**
 * @fileoverview Uma etiqueta ampliada para caber numa área da tela.
 *
 * Renderiza o MESMO `EtiquetaView` da impressão, em mm reais, e só escala o
 * resultado — o preview não tem layout próprio que possa divergir do papel.
 */
import { computed } from 'vue';

import EtiquetaView from './EtiquetaView.vue';
import type { DefinicaoEtiqueta } from '../modelo';
import type { ValoresEtiqueta } from '../campos';

const PX_POR_MM = 96 / 25.4;

const props = withDefaults(
  defineProps<{
    definicao: DefinicaoEtiqueta;
    valores: ValoresEtiqueta;
    larguraMaxPx?: number;
    alturaMaxPx?: number;
  }>(),
  { larguraMaxPx: 320, alturaMaxPx: 220 },
);

const larguraPx = computed(() => props.definicao.pagina.largura_mm * PX_POR_MM);
const alturaPx = computed(() => props.definicao.pagina.altura_mm * PX_POR_MM);
const escala = computed(() => Math.min(props.larguraMaxPx / larguraPx.value, props.alturaMaxPx / alturaPx.value, 4));
</script>

<template>
  <div
    class="relative shrink-0 rounded-sm shadow-sm ring-1 ring-zinc-300"
    :style="{ width: `${larguraPx * escala}px`, height: `${alturaPx * escala}px` }"
  >
    <div class="absolute left-0 top-0 origin-top-left" :style="{ transform: `scale(${escala})` }">
      <EtiquetaView :definicao="definicao" :valores="valores" />
    </div>
  </div>
</template>
