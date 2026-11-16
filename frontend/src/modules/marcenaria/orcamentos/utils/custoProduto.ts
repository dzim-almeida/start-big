/**
 * @fileoverview Custo de um produto do cadastro pela regra O3a (SPEC-00):
 * o último preço de compra; sem ele, o custo médio; sem os dois, "sem custo".
 *
 * Serve só para MOSTRAR o custo na busca de insumo antes de incluir (Spec 06B
 * D26). O custo que vale no orçamento é o que o backend copia ao gravar
 * (06A D2, D3), pela mesma regra.
 */
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

/** De onde veio o custo do insumo (selo da linha, D27). */
export type OrigemCusto = 'ULTIMA_COMPRA' | 'CUSTO_MEDIO' | 'SEM_CUSTO' | 'MANUAL';

/** Texto do selo de cada origem. */
export const ROTULO_ORIGEM: Record<string, string> = {
  ULTIMA_COMPRA: 'última compra',
  CUSTO_MEDIO: 'custo médio',
  SEM_CUSTO: 'sem custo',
  MANUAL: 'manual',
};

/** { centavos, origem } do produto pela regra O3a. */
export function custoPelaRegraO3a(produto: Pick<ProdutoRead, 'estoque'>): { centavos: number; origem: OrigemCusto } {
  const ultimaCompra = produto.estoque?.valor_entrada ?? 0;
  if (ultimaCompra > 0) return { centavos: ultimaCompra, origem: 'ULTIMA_COMPRA' };
  const medio = produto.estoque?.custo_medio ?? 0;
  if (medio > 0) return { centavos: medio, origem: 'CUSTO_MEDIO' };
  return { centavos: 0, origem: 'SEM_CUSTO' };
}
