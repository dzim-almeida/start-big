/**
 * @fileoverview Dispara a impressão de etiquetas.
 *
 * Dois caminhos, decididos pela configuração do terminal:
 * - DIRETO na térmica (ZPL/TSPL/EPL, fase 4): sem diálogo — ver nativo/.
 * - Pelo DRIVER do Windows: quem usa renderiza
 *   `<EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />`; o trabalho
 *   monta as páginas, o `@page` recebe o tamanho do papel e o diálogo abre.
 *   Terminada a impressão (`afterprint`), o trabalho é desmontado.
 */

import { nextTick, shallowRef } from 'vue';

import { useToast } from '@/shared/composables/useToast';
import { useImpressaoStore, type ConfigImpressao } from '@/shared/stores/impressao.store';
import { imprimirNaTermica, motivoParaDriver } from './nativo/imprimirNativo';

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
  const store = useImpressaoStore();
  const toast = useToast();

  /**
   * @param config configuração a usar no lugar da salva — o teste da tela de
   *   calibração imprime com o que está sendo editado, antes de salvar.
   */
  async function imprimir(novo: TrabalhoEtiquetas, config: ConfigImpressao = store.config): Promise<void> {
    if (novo.etiquetas.length === 0) return;

    if (motivoParaDriver(config, novo.definicao) === null) {
      try {
        await imprimirNaTermica(novo, config);
        toast.success(
          novo.etiquetas.length === 1 ? 'Etiqueta enviada à impressora' : `${novo.etiquetas.length} etiquetas enviadas à impressora`,
        );
      } catch (erro) {
        console.error('[Etiquetas] Falha na impressão direta:', erro);
        toast.error(
          'Falha ao imprimir na térmica',
          `${erro instanceof Error ? erro.message : String(erro)} — confira em "Impressora de etiquetas" (botão da régua).`,
        );
      }
      return;
    }

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
