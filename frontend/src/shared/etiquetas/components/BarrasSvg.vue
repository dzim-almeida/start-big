<script setup lang="ts">
/**
 * @fileoverview Código de barras em SVG, esticado para ocupar a caixa do elemento.
 *
 * O JsBarcode desenha em px; aqui o SVG ganha `viewBox` e
 * `preserveAspectRatio="none"` para caber exatamente nos mm do modelo. Esticar
 * na horizontal é seguro: todas as barras escalam pelo MESMO fator, e a
 * proporção entre elas — que é o que o leitor mede — não muda.
 *
 * A legenda (o número) é desenhada à parte, em HTML: a do JsBarcode esticaria
 * junto com as barras.
 */
import { computed, onMounted, ref, watch } from 'vue';
import JsBarcode from 'jsbarcode';

import { resolverCodigo, type SimbologiaPreferida } from '../codigoBarras';

const props = defineProps<{
  valor: string;
  simbologia: SimbologiaPreferida;
  legenda: boolean;
  alturaMm: number;
}>();

const svg = ref<SVGSVGElement | null>(null);
const falhou = ref(false);

const codigo = computed(() => resolverCodigo(props.valor, props.simbologia));

// Legenda de até 3,2 mm, nunca mais que 22% da altura (o resto é barra).
const alturaLegendaMm = computed(() => (props.legenda ? Math.min(3.2, props.alturaMm * 0.22) : 0));
const fonteLegendaPt = computed(() => alturaLegendaMm.value / 0.3528 / 1.15);

function desenhar() {
  const el = svg.value;
  const c = codigo.value;
  if (!el || !c) return;
  try {
    JsBarcode(el, c.valor, { format: c.simbologia, displayValue: false, margin: 0, width: 2, height: 100 });
    const largura = parseFloat(el.getAttribute('width') ?? '0');
    const altura = parseFloat(el.getAttribute('height') ?? '0');
    el.setAttribute('viewBox', `0 0 ${largura} ${altura}`);
    el.setAttribute('preserveAspectRatio', 'none');
    el.removeAttribute('width');
    el.removeAttribute('height');
    el.removeAttribute('style');
    falhou.value = false;
  } catch {
    falhou.value = true;
  }
}

onMounted(desenhar);
watch(codigo, desenhar, { flush: 'post' });
</script>

<template>
  <div v-if="!codigo" class="barras-vazio">sem código</div>
  <div v-else-if="falhou" class="barras-vazio">código inválido</div>
  <div v-else class="barras">
    <svg ref="svg" class="barras-svg" xmlns="http://www.w3.org/2000/svg" />
    <div
      v-if="legenda"
      class="barras-legenda"
      :style="{ height: `${alturaLegendaMm}mm`, fontSize: `${fonteLegendaPt}pt` }"
    >
      {{ codigo.valor }}
    </div>
  </div>
</template>

<style scoped>
.barras {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}
.barras-svg {
  display: block;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
}
.barras-legenda {
  flex: none;
  text-align: center;
  line-height: 1.15;
  letter-spacing: 0.08em;
  white-space: nowrap;
  overflow: hidden;
}
.barras-vazio {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border: 0.2mm dashed #999;
  color: #777;
  font-size: 6pt;
}
</style>
