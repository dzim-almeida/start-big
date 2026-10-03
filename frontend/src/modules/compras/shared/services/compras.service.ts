/**
 * @fileoverview API do módulo de Compras (/compras).
 *
 * Toda rota daqui responde 403 `MODULO_NAO_CONTRATADO` para loja sem o módulo
 * COMPRAS — quem chama já deve ter conferido `temModulo(MODULOS.COMPRAS)`.
 */

import api from '@/api/axios';
import type {
  BaseNecessidade,
  RelatorioCompras,
  FornecedorDoProdutoEscrita,
  FornecedorDoProdutoRead,
  FornecedorResumo,
  GerarPedidoItem,
  MensagemFornecedor,
  NecessidadeGrupo,
  ParcelaSimulada,
  PedidoEscrita,
  PedidoFiltros,
  PedidoListagem,
  PedidoRead,
  PedidoResumo,
  ProdutoParaPedido,
  RecebimentoEscrita,
} from '../types/compras.types';

export async function getFornecedoresQueVendem(): Promise<FornecedorResumo[]> {
  const { data } = await api.get<FornecedorResumo[]>('compras/fornecedores');
  return data;
}

export async function getFornecedoresDoProduto(produtoId: number): Promise<FornecedorDoProdutoRead[]> {
  const { data } = await api.get<FornecedorDoProdutoRead[]>(`compras/produtos/${produtoId}/fornecedores`);
  return data;
}

/** Replace-all: a lista inteira; o fornecedor que não vier sai do produto. */
export async function salvarFornecedoresDoProduto(
  produtoId: number,
  fornecedores: FornecedorDoProdutoEscrita[],
): Promise<FornecedorDoProdutoRead[]> {
  const { data } = await api.put<FornecedorDoProdutoRead[]>(`compras/produtos/${produtoId}/fornecedores`, {
    fornecedores,
  });
  return data;
}

// ---------------------------------------------------------------------------
// Fase 2 — necessidades e pedido de compra
// ---------------------------------------------------------------------------

/** `base` VENDAS soma a média de venda dos últimos 90 dias, cobrindo `cobertura_dias`. */
export async function getNecessidades(
  params: { base: BaseNecessidade; cobertura_dias: number } = { base: 'MINIMO', cobertura_dias: 30 },
): Promise<NecessidadeGrupo[]> {
  const { data } = await api.get<NecessidadeGrupo[]>('compras/necessidades', { params });
  return data;
}

/** Fornecedores (prazo, pontualidade, valor) e variação de preço no período. */
export async function getRelatorioCompras(inicio: string, fim: string): Promise<RelatorioCompras> {
  const { data } = await api.get<RelatorioCompras>('compras/relatorios', { params: { inicio, fim } });
  return data;
}

/** Um RASCUNHO por fornecedor. */
export async function gerarPedidos(itens: GerarPedidoItem[]): Promise<PedidoResumo[]> {
  const { data } = await api.post<PedidoResumo[]>('compras/necessidades/gerar-pedidos', { itens });
  return data;
}

export async function buscarProdutosParaPedido(busca: string): Promise<ProdutoParaPedido[]> {
  const { data } = await api.get<ProdutoParaPedido[]>('compras/produtos', { params: { busca } });
  return data;
}

export async function simularParcelas(total: number, condicao: string | null): Promise<ParcelaSimulada[]> {
  const { data } = await api.post<ParcelaSimulada[]>('compras/parcelas/simular', { total, condicao });
  return data;
}

export async function listarPedidos(filtros: PedidoFiltros): Promise<PedidoListagem> {
  const { data } = await api.get<PedidoListagem>('compras/pedidos', { params: filtros });
  return data;
}

export async function getPedido(id: number): Promise<PedidoRead> {
  const { data } = await api.get<PedidoRead>(`compras/pedidos/${id}`);
  return data;
}

export async function criarPedido(pedido: PedidoEscrita): Promise<PedidoRead> {
  const { data } = await api.post<PedidoRead>('compras/pedidos', pedido);
  return data;
}

/** Só RASCUNHO: substitui o pedido inteiro. */
export async function atualizarPedido(id: number, pedido: PedidoEscrita): Promise<PedidoRead> {
  const { data } = await api.put<PedidoRead>(`compras/pedidos/${id}`, pedido);
  return data;
}

/** Rascunho ou enviado: só previsão e observação. */
export async function atualizarDadosPedido(
  id: number,
  dados: { previsao_entrega: string | null; observacao: string | null },
): Promise<PedidoRead> {
  const { data } = await api.patch<PedidoRead>(`compras/pedidos/${id}`, dados);
  return data;
}

export async function enviarPedido(id: number): Promise<PedidoRead> {
  const { data } = await api.post<PedidoRead>(`compras/pedidos/${id}/enviar`);
  return data;
}

export async function voltarPedidoRascunho(id: number, motivo: string): Promise<PedidoRead> {
  const { data } = await api.post<PedidoRead>(`compras/pedidos/${id}/voltar-rascunho`, { motivo });
  return data;
}

export async function cancelarPedido(id: number, motivo: string): Promise<PedidoRead> {
  const { data } = await api.post<PedidoRead>(`compras/pedidos/${id}/cancelar`, { motivo });
  return data;
}

// ---------------------------------------------------------------------------
// Fase 3 — recebimento
// ---------------------------------------------------------------------------

/** Dá entrada no que chegou: estoque, último preço e (com o Financeiro) contas a pagar. */
export async function receberPedido(id: number, recebimento: RecebimentoEscrita): Promise<PedidoRead> {
  const { data } = await api.post<PedidoRead>(`compras/pedidos/${id}/recebimentos`, recebimento);
  return data;
}

/** O resto de um pedido recebido em parte não vem mais. */
export async function encerrarSaldoPedido(id: number, motivo: string): Promise<PedidoRead> {
  const { data } = await api.post<PedidoRead>(`compras/pedidos/${id}/encerrar`, { motivo });
  return data;
}

export async function getMensagemPedido(id: number): Promise<MensagemFornecedor> {
  const { data } = await api.get<MensagemFornecedor>(`compras/pedidos/${id}/whatsapp`);
  return data;
}
