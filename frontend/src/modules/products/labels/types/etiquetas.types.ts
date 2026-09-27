/**
 * @fileoverview Tipos da API de modelos de etiqueta (backend: schemas/modelo_etiqueta.py)
 */

import type { DefinicaoEtiqueta, FonteEtiqueta } from '@/shared/etiquetas/modelo';
import type { ValoresEtiqueta } from '@/shared/etiquetas/campos';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';
import type { EmbalagemRead } from '@/modules/products/inventory/types/embalagens.types';

export interface ModeloEtiquetaApi {
  id: number;
  nome: string;
  fonte: FonteEtiqueta;
  definicao: DefinicaoEtiqueta;
  data_criacao: string;
  data_atualizacao: string;
}

export interface ModeloEtiquetaPayload {
  nome: string;
  fonte: FonteEtiqueta;
  definicao: DefinicaoEtiqueta;
}

/** Um produto na fila de impressão. O produto em si é lido da listagem na hora. */
export interface ItemFilaEtiqueta {
  produtoId: number;
  quantidade: number;
  /** Etiqueta de uma embalagem (fardo/caixa); nulo = da unidade. */
  embalagemId: number | null;
}

/** Uma linha da fila já resolvida contra a listagem de produtos. */
export interface LinhaFila {
  /** produto + embalagem: a mesma lata pode estar na fila como unidade e como fardo. */
  chave: string;
  produto: ProdutoRead;
  embalagem: EmbalagemRead | null;
  /** Embalagens que dá para escolher nesta linha (vazio = só unidade). */
  embalagensDisponiveis: EmbalagemRead[];
  quantidade: number;
  valores: ValoresEtiqueta;
  /** Produto sem EAN e sem código interno: a etiqueta sai sem barras. */
  semCodigo: boolean;
}
