/**
 * Chamadas de portes e preço por porte (Spec 02A/02B do lava-rápido).
 * A resposta é conferida com zod na chegada: formato errado vira erro da query.
 */
import { z } from 'zod';

import api from '@/api/axios';

import {
  porteSchema,
  precoPorteSchema,
  servicoDoPorteSchema,
  type Porte,
  type PorteCreate,
  type PorteUpdate,
  type PrecoPorte,
  type ServicoDoPorte,
} from '../schemas/porte.schema';

const URL = '/lava-rapido';

/** Portes da loja. A primeira leitura grava a lista inicial no backend. */
export async function getPortes(incluirInativos = false): Promise<Porte[]> {
  const { data } = await api.get(`${URL}/portes`, { params: { incluir_inativos: incluirInativos } });
  return z.array(porteSchema).parse(data);
}

export async function criarPorte(dados: PorteCreate): Promise<Porte> {
  const { data } = await api.post(`${URL}/portes`, dados);
  return porteSchema.parse(data);
}

export async function atualizarPorte(id: number, dados: PorteUpdate): Promise<Porte> {
  const { data } = await api.put(`${URL}/portes/${id}`, dados);
  return porteSchema.parse(data);
}

/** Todo serviço ativo, com o preço do porte ou o padrão. */
export async function getServicosDoPorte(porteId: number): Promise<ServicoDoPorte[]> {
  const { data } = await api.get(`${URL}/portes/${porteId}/servicos`);
  return z.array(servicoDoPorteSchema).parse(data);
}

export async function getPrecosDoServico(servicoId: number): Promise<PrecoPorte[]> {
  const { data } = await api.get(`${URL}/servicos/${servicoId}/precos`);
  return z.array(precoPorteSchema).parse(data);
}

/** Grava a grade INTEIRA: porte fora da lista volta ao preço padrão. */
export async function salvarPrecosDoServico(servicoId: number, precos: PrecoPorte[]): Promise<PrecoPorte[]> {
  const { data } = await api.put(`${URL}/servicos/${servicoId}/precos`, { precos });
  return z.array(precoPorteSchema).parse(data);
}
