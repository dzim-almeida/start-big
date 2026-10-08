<script setup lang="ts">
/**
 * @fileoverview QR Code em SVG, desenhado de forma SÍNCRONA.
 *
 * O `QRCode.toString` da lib é assíncrono, e a impressão chama o
 * `window.print()` logo depois de montar as etiquetas: um QR que chegasse
 * depois sairia em branco no papel. Com `QRCode.create` a matriz sai na hora
 * e o SVG é montado aqui mesmo.
 */
import { computed } from 'vue';
import QRCode from 'qrcode';

const props = defineProps<{ valor: string }>();

const desenho = computed(() => {
  if (!props.valor) return null;
  try {
    const { modules } = QRCode.create(props.valor, { errorCorrectionLevel: 'M' });
    let caminho = '';
    for (let linha = 0; linha < modules.size; linha++) {
      for (let coluna = 0; coluna < modules.size; coluna++) {
        if (modules.get(linha, coluna)) caminho += `M${coluna} ${linha}h1v1h-1z`;
      }
    }
    return { tamanho: modules.size, caminho };
  } catch {
    return null;
  }
});
</script>

<template>
  <svg
    v-if="desenho"
    :viewBox="`0 0 ${desenho.tamanho} ${desenho.tamanho}`"
    class="qr"
    shape-rendering="crispEdges"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path :d="desenho.caminho" fill="#000" />
  </svg>
</template>

<style scoped>
.qr {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
