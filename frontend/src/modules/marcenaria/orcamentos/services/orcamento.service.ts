/**
 * @fileoverview Chamadas do orçamento de marcenaria: lista, cabeçalho,
 * transições, versões, histórico e projetos (Spec 06A §6.1).
 *
 * Toda ESCRITA manda `?revisao=N` (trava otimista, 06A D20) e devolve o
 * DETALHE completo (06A D21), conferido pelo zod.
 */
import api from '@/api/axios';

import {
  contagensSchema,
  eventoSchema,
  listaSchema,
  orcamentoDetalheSchema,
  projetoSchema,
  versaoSchema,
  type ContagensOrcamento,
  type EventoOrcamento,
  type ListaOrcamentos,
  type OrcamentoDetalhe,
  type ProjetoCliente,
  type VersaoOrcamento,
} from '../schemas/orcamentoDetalhe.schema';
import type { CabecalhoForm } from '../utils/diferencaCabecalho';

export const URL_ORCAMENTOS = '/marcenaria/orcamentos';

/** Filtros da lista (06A §6.3). */
export interface FiltrosLista {
  status?: string | null;
  cliente?: number | null;
  vendedor_id?: number | null;
  vence_em_dias?: number | null;
  busca?: string | null;
  incluir_versoes_antigas?: boolean;
  page?: number;
  limit?: number;
}

/** Tira os filtros vazios (o backend recusaria "status=" vazio). */
function semVazios(filtros: FiltrosLista): Record<string, unknown> {
  return Object.fromEntries(Object.entries(filtros).filter(([, v]) => v !== null && v !== undefined && v !== ''));
}

const detalhe = (data: unknown): OrcamentoDetalhe => orcamentoDetalheSchema.parse(data);

// ---------------------------------------------------------------------------
// Leitura
// ---------------------------------------------------------------------------

export async function listarOrcamentos(filtros: FiltrosLista): Promise<ListaOrcamentos> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/`, { params: semVazios(filtros) });
  return listaSchema.parse(data);
}

export async function getContagens(): Promise<ContagensOrcamento> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/contagens`);
  return contagensSchema.parse(data);
}

export async function getOrcamento(id: number): Promise<OrcamentoDetalhe> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/${id}`);
  return detalhe(data);
}

export async function getVersoes(id: number): Promise<VersaoOrcamento[]> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/${id}/versoes`);
  return versaoSchema.array().parse(data);
}

export async function getHistorico(id: number): Promise<EventoOrcamento[]> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/${id}/historico`);
  return eventoSchema.array().parse(data);
}

/** Projetos (objetos) ativos do cliente, para escolher (06A §6.7). */
export async function getProjetosDoCliente(clienteId: number): Promise<ProjetoCliente[]> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/projetos`, { params: { cliente_id: clienteId } });
  return projetoSchema.array().parse(data);
}

// ---------------------------------------------------------------------------
// Escrita do cabeçalho
// ---------------------------------------------------------------------------

/** Cria em RASCUNHO; os parâmetros vêm copiados da configuração (06A D4). */
export async function criarOrcamento(corpo: Partial<CabecalhoForm>): Promise<OrcamentoDetalhe> {
  const permitidos = ['cliente_id', 'objeto_id', 'projeto_nome', 'endereco_obra', 'funcionario_id'] as const;
  const enviado = Object.fromEntries(permitidos.filter((k) => corpo[k] != null).map((k) => [k, corpo[k]]));
  const { data } = await api.post(`${URL_ORCAMENTOS}/`, enviado);
  return detalhe(data);
}

/** PATCH: só os campos que mudaram (06B D8). */
export async function patchOrcamento(id: number, revisao: number, mudancas: Partial<CabecalhoForm>): Promise<OrcamentoDetalhe> {
  const { data } = await api.patch(`${URL_ORCAMENTOS}/${id}`, mudancas, { params: { revisao } });
  return detalhe(data);
}

export async function excluirOrcamento(id: number, revisao: number): Promise<void> {
  await api.delete(`${URL_ORCAMENTOS}/${id}`, { params: { revisao } });
}

/** Arquitetos do orçamento (09B): sem `rt_bp`, o backend mantém o gravado ou usa o padrão. */
export async function putRt(
  id: number,
  revisao: number,
  arquitetos: { fornecedor_id: number; rt_bp?: number }[],
): Promise<OrcamentoDetalhe> {
  const { data } = await api.put(`${URL_ORCAMENTOS}/${id}/rt`, { arquitetos }, { params: { revisao } });
  return detalhe(data);
}

// ---------------------------------------------------------------------------
// Transições (06A D12-D17)
// ---------------------------------------------------------------------------

async function transicao(id: number, revisao: number, acao: string, corpo?: unknown): Promise<OrcamentoDetalhe> {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/${acao}`, corpo, { params: { revisao } });
  return detalhe(data);
}

export const enviarOrcamento = (id: number, revisao: number) => transicao(id, revisao, 'enviar');
export const voltarAEditar = (id: number, revisao: number) => transicao(id, revisao, 'voltar-a-editar');
export const recusarOrcamento = (id: number, revisao: number, motivo: string) =>
  transicao(id, revisao, 'recusar', { motivo });
export const renovarOrcamento = (id: number, revisao: number) => transicao(id, revisao, 'renovar');
/** Devolve o detalhe da versão NOVA. */
export const novaVersao = (id: number, revisao: number) => transicao(id, revisao, 'nova-versao');
