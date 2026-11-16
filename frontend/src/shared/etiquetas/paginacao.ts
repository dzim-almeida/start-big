/**
 * @fileoverview Distribui as etiquetas nas páginas do papel.
 *
 * Separado do componente para ser testável: é aqui que mora o "pular N
 * posições" da folha meio usada (E6) — errar a conta aqui imprime em cima da
 * etiqueta que já foi arrancada.
 */

import { etiquetasPorPagina, type PaginaEtiqueta } from './modelo';

export interface Posicionada<T> {
  /** Índice da posição dentro da página (0 = canto superior esquerdo). */
  posicao: number;
  item: T;
}

/**
 * @param pular posições já usadas no INÍCIO da primeira folha. Ignorado na
 *   bobina, que não tem "folha usada".
 */
export function paginar<T>(pagina: PaginaEtiqueta, itens: T[], pular = 0): Posicionada<T>[][] {
  const porPagina = etiquetasPorPagina(pagina);
  const deslocamento = pagina.tipo === 'folha' ? Math.max(0, Math.min(pular, porPagina - 1)) : 0;

  const paginas: Posicionada<T>[][] = [];
  itens.forEach((item, i) => {
    const absoluta = i + deslocamento;
    const numeroPagina = Math.floor(absoluta / porPagina);
    (paginas[numeroPagina] ??= []).push({ posicao: absoluta % porPagina, item });
  });
  return paginas;
}

/** Repete cada item pela sua quantidade, na ordem da fila. */
export function expandir<T>(itens: { item: T; quantidade: number }[]): T[] {
  return itens.flatMap(({ item, quantidade }) => Array.from({ length: Math.max(0, quantidade) }, () => item));
}
