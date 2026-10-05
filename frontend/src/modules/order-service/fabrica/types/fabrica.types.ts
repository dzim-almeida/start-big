/**
 * @fileoverview Tipos da marcenaria-fábrica (backend: app/schemas/fabrica.py).
 */

/** M2 = chapa (rende mm²), M = fita/perfil (rende mm), UN = ferragem. */
export type UnidadeConsumo = 'M2' | 'M' | 'UN';

export interface InsumoRead {
  produto_id: number;
  /** Unidade do ESTOQUE — a de compra (chapa, rolo, UN). */
  unidade_medida: string | null;
  /** `null` = o produto não é insumo. */
  unidade_consumo: UnidadeConsumo | null;
  /** Rendimento de uma unidade de estoque: mm² (M2), mm (M) ou unidades (UN). */
  consumo_por_unidade: number | null;
  sofre_perda: boolean;
}

export interface InsumoEscrita {
  unidade_consumo: UnidadeConsumo | null;
  consumo_por_unidade: number | null;
  sofre_perda: boolean;
}
