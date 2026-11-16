/**
 * @fileoverview Conversões da tela de insumo: o que o lojista digita (mm da
 * chapa, metros do rolo) ↔ o inteiro que o backend guarda (mm², mm).
 *
 * O backend guarda inteiro de propósito (plano, D4): é com ele que a
 * aprovação do orçamento calcula quantas chapas comprar.
 */

import type { UnidadeConsumo } from '../types/fabrica.types';

const MM2_POR_M2 = 1_000_000;
const MM_POR_M = 1_000;

/** Área da chapa em mm², a partir das medidas em mm. `null` se faltar medida. */
export function areaDaChapa(larguraMm: number | null, alturaMm: number | null): number | null {
  if (!larguraMm || !alturaMm || larguraMm <= 0 || alturaMm <= 0) return null;
  return Math.round(larguraMm) * Math.round(alturaMm);
}

/** Comprimento do rolo em mm, a partir de metros. */
export function comprimentoEmMm(metros: number | null): number | null {
  if (!metros || metros <= 0) return null;
  return Math.round(metros * MM_POR_M);
}

/** "5,0875 m²", "50 m", "100 un" — o rendimento para ler. */
export function descreverRendimento(unidade: UnidadeConsumo, valor: number | null): string {
  if (valor == null) return '—';
  const fmt = (n: number, casas: number) => n.toLocaleString('pt-BR', { maximumFractionDigits: casas });
  if (unidade === 'M2') return `${fmt(valor / MM2_POR_M2, 4)} m²`;
  if (unidade === 'M') return `${fmt(valor / MM_POR_M, 3)} m`;
  return `${fmt(valor, 0)} un`;
}
