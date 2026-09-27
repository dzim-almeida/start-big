<script setup lang="ts">
/**
 * @fileoverview As páginas de etiquetas que vão para o papel (saída "driver
 * do Windows", plano §5.4).
 *
 * Teleportado para o body e marcado `.print-container`: é a classe que os CSS
 * de impressão globais (print-a4.css, print-cupom.css) deixam visível — todo o
 * resto do body some na impressão. O `print-etiquetas.css` zera o padding de
 * documento que o print-a4 dá ao `.print-container`.
 *
 * Só existe enquanto há um trabalho de impressão (quem monta é
 * `useImpressaoEtiquetas`), e fica `hidden` na tela.
 */
import { computed } from 'vue';

import EtiquetaView from './EtiquetaView.vue';
import { posicaoNaPagina, tamanhoDoPapel, type DefinicaoEtiqueta } from '../modelo';
import { paginar } from '../paginacao';
import type { ValoresEtiqueta } from '../campos';

import '../styles/print-etiquetas.css';

const props = defineProps<{
  definicao: DefinicaoEtiqueta;
  etiquetas: ValoresEtiqueta[];
  pular: number;
  /** Calibração do terminal (mm): empurra tudo para a direita/baixo. */
  deslocamentoX: number;
  deslocamentoY: number;
  contorno?: boolean;
}>();

const papel = computed(() => tamanhoDoPapel(props.definicao.pagina));
const paginas = computed(() => paginar(props.definicao.pagina, props.etiquetas, props.pular));

// Meio milímetro a menos que o papel: uma página de altura EXATA transborda
// por arredondamento e o Chromium solta uma página em branco entre as
// etiquetas — no rolo, isso é uma etiqueta desperdiçada a cada uma impressa.
const estiloPagina = computed(() => ({
  width: `${papel.value.largura_mm}mm`,
  height: `${papel.value.altura_mm - 0.5}mm`,
}));

function estiloPosicao(posicao: number) {
  const { x, y } = posicaoNaPagina(props.definicao.pagina, posicao);
  return { left: `${x + props.deslocamentoX}mm`, top: `${y + props.deslocamentoY}mm` };
}
</script>

<template>
  <Teleport to="body">
    <div class="print-container etiquetas-print hidden print:block">
      <div v-for="(pagina, n) in paginas" :key="n" class="etiquetas-pagina" :style="estiloPagina">
        <div v-for="{ posicao, item } in pagina" :key="posicao" class="etiquetas-posicao" :style="estiloPosicao(posicao)">
          <EtiquetaView :definicao="definicao" :valores="item" :contorno="contorno" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
