<script setup lang="ts">
/**
 * @fileoverview UMA etiqueta renderizada em HTML, em milímetros reais.
 *
 * É o renderizador "driver do Windows" do plano (§5.4): o mesmo componente
 * serve o preview da tela e a impressão — o que se vê é o que sai (E5).
 */
import { computed } from 'vue';

import type { DefinicaoEtiqueta, ElementoEtiqueta, ElementoTexto } from '../modelo';
import { valorDoCodigo, type ValoresEtiqueta } from '../campos';
import BarrasSvg from './BarrasSvg.vue';
import QrSvg from './QrSvg.vue';

const props = defineProps<{
  definicao: DefinicaoEtiqueta;
  valores: ValoresEtiqueta;
  /** Contorno pontilhado da etiqueta — para o preview, nunca no papel. */
  contorno?: boolean;
}>();

const estiloEtiqueta = computed(() => ({
  width: `${props.definicao.pagina.largura_mm}mm`,
  height: `${props.definicao.pagina.altura_mm}mm`,
}));

function caixa(el: ElementoEtiqueta) {
  return { left: `${el.x}mm`, top: `${el.y}mm`, width: `${el.w}mm`, height: `${el.h}mm` };
}

function texto(el: ElementoTexto): string {
  const valor = el.campo ? (props.valores[el.campo] ?? '') : '';
  // Campo vazio não imprime o prefixo sozinho ("Cód. " sem código).
  if (el.campo && !valor) return '';
  return `${el.texto ?? ''}${valor}`;
}

const ALINHAMENTO = { esquerda: 'left', centro: 'center', direita: 'right' } as const;

function estiloTexto(el: ElementoTexto) {
  const linhas = el.linhas_max ?? 1;
  return {
    fontSize: `${el.fonte_pt}pt`,
    fontWeight: el.negrito ? 700 : 400,
    textAlign: ALINHAMENTO[el.alinhamento ?? 'esquerda'],
    WebkitLineClamp: linhas,
    whiteSpace: linhas === 1 ? 'nowrap' : 'normal',
  };
}
</script>

<template>
  <div class="etiqueta" :class="{ 'etiqueta--contorno': contorno }" :style="estiloEtiqueta">
    <template v-for="(el, i) in definicao.elementos" :key="i">
      <div v-if="el.tipo === 'texto'" class="el el-texto" :style="caixa(el)">
        <div class="el-texto-conteudo" :style="estiloTexto(el)">{{ texto(el) }}</div>
      </div>

      <div v-else-if="el.tipo === 'barras'" class="el" :style="caixa(el)">
        <BarrasSvg
          :valor="valorDoCodigo(valores, el.campo)"
          :simbologia="el.simbologia"
          :legenda="el.legenda"
          :altura-mm="el.h"
        />
      </div>

      <div v-else-if="el.tipo === 'qr'" class="el" :style="caixa(el)">
        <QrSvg :valor="valores[el.campo] ?? ''" />
      </div>

      <div
        v-else-if="el.tipo === 'linha'"
        class="el"
        :style="{ ...caixa(el), height: '0', borderTop: `${el.espessura_mm}mm solid #000` }"
      />

      <div v-else-if="el.tipo === 'caixa'" class="el" :style="{ ...caixa(el), border: `${el.espessura_mm}mm solid #000` }" />
    </template>
  </div>
</template>

<style scoped>
.etiqueta {
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  background: #fff;
  color: #000;
  font-family: Arial, Helvetica, sans-serif;
}
.etiqueta--contorno {
  outline: 1px dashed #a1a1aa;
}
.el {
  position: absolute;
  box-sizing: border-box;
}
.el-texto {
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}
.el-texto-conteudo {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
</style>
