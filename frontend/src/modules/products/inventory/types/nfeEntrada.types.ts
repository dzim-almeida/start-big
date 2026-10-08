/**
 * @fileoverview Entrada de mercadoria pela XML da NF-e.
 * Espelho de `backend-fastapi/app/schemas/nfe_entrada.py`. Dinheiro em centavos.
 */

export interface FiscalSugerido {
  ncm: string | null;
  cest: string | null;
  csosn: string | null;
  cst_icms: string | null;
  cfop_padrao: string | null;
  icms_st: boolean;
  monofasico: boolean;
}

export interface ItemPrevia {
  indice: number;
  codigo: string;
  descricao: string;
  ean: string | null;
  ean_tributavel: string | null;
  unidade: string;
  quantidade: number;
  /** Com IPI, ST, frete e desconto. */
  custo_total: number;
  reconhecido_por: 'vinculo' | 'embalagem' | 'codigo_barras' | null;
  produto: {
    id: number;
    nome: string;
    codigo_produto: string | null;
    custo_atual: number | null;
    valor_varejo: number | null;
  } | null;
  embalagem_id: number | null;
  embalagem_sigla: string | null;
  fator: number;
  fator_da_nota: number;
  /** A unidade da nota é CX, FD, PCT… (tem várias unidades dentro). */
  unidade_de_embalagem: boolean;
  /** Embalagem sem o fator dito em lugar nenhum: precisa informar ou confirmar 1. */
  fator_a_confirmar: boolean;
  fiscal_sugerido: FiscalSugerido;
  /** Módulo Compras: divergências com o pedido sugerido. Ausente/vazio sem o módulo. */
  pedido_avisos?: string[];
}

/** Pedido enviado/parcial do fornecedor da nota (módulo Compras). */
export interface PedidoAbertoPrevia {
  id: number;
  codigo: string;
  situacao: string;
  previsao_entrega: string | null;
  quantidade_itens: number;
}

export interface NotaPrevia {
  chave: string;
  numero: string;
  serie: string;
  emissao: string | null;
  natureza: string | null;
  valor_total: number;
  fornecedor: { id: number | null; documento: string | null; nome: string | null; fantasia: string | null };
  itens: ItemPrevia[];
  duplicatas: { numero: string; vencimento: string; valor: number }[];
  financeiro_disponivel: boolean;
  ja_importada_em: string | null;
  avisos: string[];
  // Módulo Compras (opcionais: backend sem o módulo, ou antigo, não manda).
  pedidos_abertos?: PedidoAbertoPrevia[];
  pedido_sugerido_id?: number | null;
  /** Do pedido sugerido: o que ele esperava e não veio. */
  pedido_avisos?: string[];
}

export interface DecisaoItem {
  indice: number;
  acao: 'vincular' | 'criar' | 'ignorar';
  produto_id?: number;
  embalagem_id?: number | null;
  fator: number;
  /** "É 1 mesmo": cada CX/FD da nota é uma unidade do estoque. */
  fator_confirmado?: boolean;
  novo?: {
    nome: string;
    codigo_produto: string;
    codigo_barras: string | null;
    unidade_medida: string;
    valor_varejo: number;
    usar_fiscal_sugerido: boolean;
  };
}

export interface ResultadoImportacao {
  nota_entrada_id: number;
  fornecedor_id: number | null;
  fornecedor_criado: boolean;
  itens_lancados: number;
  itens_ignorados: number;
  produtos_criados: number;
  contas_pagar_lancadas: number;
  movimentacao_ids: number[];
  entradas: { produto_id: number; unidades: number }[];
  // Módulo Compras: o pedido ligado e o que divergiu (só aviso).
  pedido_codigo?: string | null;
  pedido_situacao?: string | null;
  pedido_avisos?: string[];
}
