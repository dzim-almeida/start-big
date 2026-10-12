/**
 * @fileoverview Chamadas dos ambientes e móveis do orçamento (Spec 06A §6.1,
 * §6.4 e §6.6). Toda escrita manda a revisão e devolve o detalhe completo.
 */
import api from '@/api/axios';

import { orcamentoDetalheSchema, simulacaoSchema, type OrcamentoDetalhe, type SimulacaoMovel } from '../schemas/orcamentoDetalhe.schema';
import { URL_ORCAMENTOS } from './orcamento.service';

/** Corpo do móvel como a API recebe (06A §6.4). Chave de custo AUSENTE mantém o gravado (D24a). */
export interface MovelEntrada {
  nome: string;
  descricao?: string | null;
  largura_mm?: number | null;
  altura_mm?: number | null;
  profundidade_mm?: number | null;
  quantidade: number;
  tipo_producao: 'INTERNA' | 'TERCEIRIZADA';
  central_fornecedor_id?: number | null;
  terceirizado_centavos?: number;
  mao_obra?: { modo: 'FIXA' | 'HORAS' | 'NENHUMA'; centavos: number; horas_centesimos: number };
  insumos: { id?: number; produto_id?: number | null; quantidade_milesimos: number; custo_unit_centavos?: number }[];
  ambiente_id?: number;
}

const detalhe = (data: unknown): OrcamentoDetalhe => orcamentoDetalheSchema.parse(data);
const cfg = (revisao: number) => ({ params: { revisao } });

// --- Ambientes ---------------------------------------------------------------

export async function criarAmbiente(id: number, revisao: number, nome: string) {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/ambientes`, { nome }, cfg(revisao));
  return detalhe(data);
}

export async function renomearAmbiente(id: number, ambienteId: number, revisao: number, nome: string) {
  const { data } = await api.patch(`${URL_ORCAMENTOS}/${id}/ambientes/${ambienteId}`, { nome }, cfg(revisao));
  return detalhe(data);
}

export async function removerAmbiente(id: number, ambienteId: number, revisao: number) {
  const { data } = await api.delete(`${URL_ORCAMENTOS}/${id}/ambientes/${ambienteId}`, cfg(revisao));
  return detalhe(data);
}

export async function ordenarAmbientes(id: number, revisao: number, ids: number[]) {
  const { data } = await api.put(`${URL_ORCAMENTOS}/${id}/ambientes/ordem`, { ids }, cfg(revisao));
  return detalhe(data);
}

// --- Móveis ------------------------------------------------------------------

export async function criarMovel(id: number, ambienteId: number, revisao: number, movel: MovelEntrada) {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/ambientes/${ambienteId}/moveis`, movel, cfg(revisao));
  return detalhe(data);
}

export async function salvarMovel(id: number, movelId: number, revisao: number, movel: MovelEntrada) {
  const { data } = await api.put(`${URL_ORCAMENTOS}/${id}/moveis/${movelId}`, movel, cfg(revisao));
  return detalhe(data);
}

export async function removerMovel(id: number, movelId: number, revisao: number) {
  const { data } = await api.delete(`${URL_ORCAMENTOS}/${id}/moveis/${movelId}`, cfg(revisao));
  return detalhe(data);
}

export async function duplicarMovel(id: number, movelId: number, revisao: number) {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/moveis/${movelId}/duplicar`, undefined, cfg(revisao));
  return detalhe(data);
}

export async function ordenarMoveis(id: number, ambienteId: number, revisao: number, ids: number[]) {
  const { data } = await api.put(`${URL_ORCAMENTOS}/${id}/ambientes/${ambienteId}/moveis/ordem`, { ids }, cfg(revisao));
  return detalhe(data);
}

/** Prévia do preço sem gravar e sem revisão (06A §6.6). `movelId` mantém o custo copiado dos insumos com id. */
export async function simularMovel(id: number, movel: MovelEntrada, movelId?: number | null): Promise<SimulacaoMovel> {
  const corpo = { ...movel, ...(movelId ? { movel_id: movelId } : {}) };
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/moveis/simular`, corpo);
  return simulacaoSchema.parse(data);
}
