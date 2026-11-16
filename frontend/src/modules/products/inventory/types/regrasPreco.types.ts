/**
 * @fileoverview Regras de preço por quantidade do produto (plano de embalagens, §6.1).
 * Espelho de `backend-fastapi/app/schemas/produto_regra_preco.py`.
 *
 * - FAIXA (R2): "a partir de `quantidade` un, cada uma sai por `preco`".
 * - LEVE_PAGUE (R3): "leve `quantidade`, pague `pague`", com vigência.
 */

export type TipoRegraPreco = 'FAIXA' | 'LEVE_PAGUE';

export interface RegraPrecoEscrita {
  id?: number;
  tipo: TipoRegraPreco;
  quantidade: number;
  /** FAIXA: centavos por unidade. */
  preco: number | null;
  /** LEVE_PAGUE: pague Y. */
  pague: number | null;
  /** AAAA-MM-DD, inclusive. */
  inicio: string | null;
  fim: string | null;
  ativo: boolean;
}

export interface RegraPrecoRead extends RegraPrecoEscrita {
  id: number;
  produto_id: number;
}
