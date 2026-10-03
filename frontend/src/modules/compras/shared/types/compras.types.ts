/**
 * @fileoverview Tipos do módulo de Compras.
 * Espelho de `backend-fastapi/app/schemas/compras.py`.
 *
 * Dinheiro em centavos; preço por UNIDADE DE COMPRA (o fardo, se compra em fardo).
 */

/** Para o seletor de fornecedor — só quem vende mercadoria e está ativo. */
export interface FornecedorResumo {
  id: number;
  nome: string;
  nome_fantasia: string | null;
}

/** Uma linha da aba Fornecedores do produto. */
export interface FornecedorDoProdutoRead {
  /** Nulo = o fornecedor principal do cadastro, ainda sem linha própria. */
  id: number | null;
  fornecedor_id: number;
  fornecedor_nome: string;
  codigo_fornecedor: string | null;
  embalagem_id: number | null;
  embalagem_sigla: string | null;
  /** Unidades do produto por unidade de compra. */
  fator: number;
  /** Centavos por unidade de compra; nulo para quem não pode ver custo. */
  ultimo_preco: number | null;
  /** Centavos por unidade do produto (com casas: só para exibir). */
  preco_unidade: number | null;
  /** Data pura (YYYY-MM-DD). */
  ultima_compra_em: string | null;
  prazo_dias: number | null;
  /** É o fornecedor principal do cadastro do produto. */
  padrao: boolean;
  /** Menor preço por unidade entre os que têm preço (só com 2 ou mais). */
  mais_barato: boolean;
  /** Quanto está acima do mais barato, em pontos-base (476 = 4,76%). */
  acima_do_menor_bp: number;
}

/** O que a tela manda no PUT (replace-all pela chave `fornecedor_id`). */
export interface FornecedorDoProdutoEscrita {
  fornecedor_id: number;
  codigo_fornecedor: string | null;
  embalagem_id: number | null;
  fator: number;
  ultimo_preco: number | null;
  prazo_dias: number | null;
  padrao: boolean;
}

// ---------------------------------------------------------------------------
// Fase 2 — pedido de compra e necessidades
// ---------------------------------------------------------------------------
// Campos de dinheiro vêm NULOS para quem não pode ver custo (plano, D14).

export type SituacaoPedido = 'RASCUNHO' | 'ENVIADO' | 'PARCIAL' | 'RECEBIDO' | 'CANCELADO';

export interface PedidoItemRead {
  id: number;
  produto_id: number | null;
  descricao: string;
  codigo_fornecedor: string | null;
  embalagem_id: number | null;
  /** FD, CX, UN… */
  unidade_compra: string;
  fator: number;
  quantidade: number;
  quantidade_recebida: number;
  quantidade_cancelada: number;
  custo_unitario: number | null;
  subtotal: number | null;
  /** Unidades de compra que ainda não chegaram nem foram encerradas. */
  pendente: number;
  /** O que o leitor pode bipar: o código da embalagem primeiro, depois os do produto. */
  codigos_barras: string[];
}

export interface RecebimentoItemRead {
  descricao: string;
  unidade_compra: string;
  fator: number;
  quantidade: number;
  /** O que entrou no estoque (quantidade × fator). */
  unidades: number;
  custo_unitario: number | null;
}

export interface RecebimentoRead {
  id: number;
  recebido_em: string;
  recebido_por_nome: string | null;
  numero_nota: string | null;
  observacao: string | null;
  valor_itens: number | null;
  valor_ajuste: number | null;
  valor_total: number | null;
  contas_pagar_lancadas: number;
  itens: RecebimentoItemRead[];
}

export interface RecebimentoEscrita {
  itens: { pedido_item_id: number; quantidade: number; custo_unitario: number | null }[];
  numero_nota: string | null;
  observacao: string | null;
  lancar_contas_pagar: boolean;
  /** O que não chegou agora não vem mais. */
  encerrar_saldo: boolean;
}

export interface PedidoParcelaRead {
  numero: number;
  dias: number;
  valor: number | null;
}

export interface CompraLogRead {
  acao: string;
  situacao_anterior: string | null;
  situacao_nova: string | null;
  motivo: string | null;
  usuario_nome: string | null;
  ocorrido_em: string;
}

export interface PedidoResumo {
  id: number;
  numero: number;
  /** "PC-000123" */
  codigo: string;
  situacao: SituacaoPedido;
  fornecedor_id: number | null;
  fornecedor_nome: string;
  previsao_entrega: string | null;
  /** Enviado e com a previsão já passada. */
  atrasado: boolean;
  quantidade_itens: number;
  valor_total: number | null;
  criado_em: string;
  enviado_em: string | null;
}

export interface PedidoRead extends PedidoResumo {
  tipo: string;
  condicao_pagamento: string | null;
  frete: number | null;
  desconto: number | null;
  valor_itens: number | null;
  observacao: string | null;
  motivo_cancelamento: string | null;
  criado_por_nome: string | null;
  /** Com DDI 55, só dígitos. */
  fornecedor_telefone: string | null;
  itens: PedidoItemRead[];
  parcelas: PedidoParcelaRead[];
  historico: CompraLogRead[];
  recebimentos: RecebimentoRead[];
}

export interface PedidoListagem {
  itens: PedidoResumo[];
  total_itens: number;
}

export interface PedidoFiltros {
  situacao?: SituacaoPedido;
  fornecedor_id?: number;
  busca?: string;
  /** Só enviados e recebidos em parte (tela de Recebimento). */
  a_receber?: boolean;
  limit: number;
  offset: number;
}

export interface PedidoItemEscrita {
  produto_id: number;
  embalagem_id: number | null;
  fator: number;
  quantidade: number;
  custo_unitario: number;
}

export interface PedidoParcelaEscrita {
  dias: number;
  valor: number;
}

export interface PedidoEscrita {
  fornecedor_id: number;
  previsao_entrega: string | null;
  condicao_pagamento: string | null;
  frete: number;
  desconto: number;
  observacao: string | null;
  itens: PedidoItemEscrita[];
  /** `null` = o backend gera pela condição de pagamento. */
  parcelas: PedidoParcelaEscrita[] | null;
}

export interface MensagemFornecedor {
  texto: string;
  telefone: string | null;
}

export interface ParcelaSimulada {
  numero: number;
  dias: number;
  valor: number;
}

export interface EmbalagemResumo {
  id: number;
  sigla: string;
  fator: number;
}

/** Produto para pôr no pedido (busca do próprio módulo, sem exigir a permissão de Produtos). */
export interface ProdutoParaPedido {
  id: number;
  nome: string;
  codigo_produto: string | null;
  codigo_barras: string | null;
  unidade_medida: string;
  saldo: number;
  embalagens: EmbalagemResumo[];
}

export interface AlternativaMaisBarata {
  fornecedor_id: number;
  fornecedor_nome: string;
  /** Centavos por unidade do produto (com casas). */
  preco_unidade: number;
  /** Quanto é mais barato, em pontos-base (486 = 4,86%). */
  economia_bp: number;
}

export interface OpcaoFornecedor {
  fornecedor_id: number;
  fornecedor_nome: string;
  embalagem_id: number | null;
  unidade_compra: string;
  fator: number;
  ultimo_preco: number | null;
  prazo_dias: number | null;
}

export interface NecessidadeItem {
  produto_id: number;
  produto_nome: string;
  codigo_produto: string | null;
  unidade_medida: string;
  saldo: number;
  minimo: number;
  ideal: number | null;
  /** A caminho (pedidos enviados), na unidade do produto. */
  em_pedido: number;
  /** Em rascunhos — NÃO desconta da sugestão, mas avisa. */
  em_rascunho: number;
  rascunhos: string[];
  fornecedor_id: number | null;
  fornecedor_nome: string | null;
  embalagem_id: number | null;
  unidade_compra: string;
  fator: number;
  /** Unidades de compra sugeridas. */
  sugestao: number;
  ultimo_preco: number | null;
  alternativa: AlternativaMaisBarata | null;
  opcoes: OpcaoFornecedor[];
}

export interface NecessidadeGrupo {
  fornecedor_id: number | null;
  fornecedor_nome: string;
  itens: NecessidadeItem[];
}

export interface GerarPedidoItem {
  produto_id: number;
  fornecedor_id: number;
  quantidade: number;
}
