/**
 * @fileoverview Embalagens do produto (fardo, caixa, pack).
 * Espelho de `backend-fastapi/app/schemas/produto_embalagem.py`.
 */

export interface EmbalagemRead {
  id: number;
  produto_id: number;
  /** FD, CX, PCT… (vai no uCom da nota). */
  sigla: string;
  descricao: string | null;
  /** Quantas unidades do produto a embalagem tem. 1 = código de barras adicional da unidade. */
  fator: number;
  codigo_barras: string | null;
  /** Preço próprio, em centavos. */
  preco: number | null;
  /** Alternativa ao preço próprio: desconto sobre fator × unidade, em centésimos de % (500 = 5%). */
  desconto_bp: number | null;
  vende_no_pdv: boolean;
  usa_na_entrada: boolean;
  ativo: boolean;
}

/** O que a tela manda no PUT (replace-all). Sem `id` = embalagem nova. */
export interface EmbalagemEscrita {
  id?: number;
  sigla: string;
  descricao: string | null;
  fator: number;
  codigo_barras: string | null;
  preco: number | null;
  desconto_bp: number | null;
  vende_no_pdv: boolean;
  usa_na_entrada: boolean;
  ativo: boolean;
  gerar_codigo_interno?: boolean;
}
