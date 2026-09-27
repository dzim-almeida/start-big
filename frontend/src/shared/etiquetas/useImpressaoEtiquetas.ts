/**
 * @fileoverview Dispara a impressão de etiquetas pelo driver do Windows.
 *
 * Quem usa renderiza `<EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />`
 * e chama `imprimir(...)`: o trabalho monta as páginas, o `@page` recebe o
 * tamanho do papel da etiqueta e o diálogo do Windows abre. Terminada a
 * impressão (`afterprint`), o trabalho é desmontado.
 */

import { nextTick, shallowRef } from 'vue';

import { tamanhoDoPapel, type DefinicaoEtiqueta } from './modelo';
import type { ValoresEtiqueta } from './campos';

export interface TrabalhoEtiquetas {
  definicao: DefinicaoEtiqueta;
  etiquetas: ValoresEtiqueta[];
  pular: number;
  deslocamentoX: number;
  deslocamentoY: number;
  contorno?: boolean;
}

/**
 * Força o `@page` no tamanho do papel da etiqueta e abre o diálogo.
 *
 * Mesmo mecanismo de `imprimirComPagina` (print.utils.ts): a regra entra por
 * ÚLTIMO no <head>, e por isso vence o `size: A4` do print-a4.css. As sobras
 * de uma impressão anterior saem antes — inclusive as que ela deixou.
 */
export function imprimirNoPapel(tamanho: { largura_mm: number; altura_mm: number }, aoTerminar?: () => void): void {
  document.querySelectorAll('style[data-print-page]').forEach((s) => s.remove());

  const style = document.createElement('style');
  style.setAttribute('data-print-page', '');
  style.textContent = `@media print{@page{size:${tamanho.largura_mm}mm ${tamanho.altura_mm}mm;margin:0}}`;
  document.head.appendChild(style);

  const limpar = () => {
    style.remove();
    window.removeEventListener('afterprint', limpar);
    aoTerminar?.();
  };
  window.addEventListener('afterprint', limpar);
  window.print();
}

function proximoQuadro(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

export function useImpressaoEtiquetas() {
  const trabalho = shallowRef<TrabalhoEtiquetas | null>(null);

  async function imprimir(novo: TrabalhoEtiquetas): Promise<void> {
    if (novo.etiquetas.length === 0) return;
    trabalho.value = novo;
    // Monta as páginas (os códigos de barras desenham no onMounted) e deixa o
    // navegador aplicar o layout antes de fotografar a página.
    await nextTick();
    await proximoQuadro();
    imprimirNoPapel(tamanhoDoPapel(novo.definicao.pagina), () => {
      trabalho.value = null;
    });
  }

  return { trabalho, imprimir };
}
