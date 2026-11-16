/**
 * Chamadas da agenda (Spec 08A/08B do lava-rápido).
 */
import { z } from 'zod';

import api from '@/api/axios';

import {
  agendamentoSchema,
  type Agendamento,
  type AgendamentoEntrada,
  type SituacaoAgenda,
} from '../schemas/agenda.schema';

const URL = '/lava-rapido/agendamentos';

/** Agendamentos dos dias [inicio, fim] ("AAAA-MM-DD", dias da loja). */
export async function getAgendamentos(inicio: string, fim: string): Promise<Agendamento[]> {
  const { data } = await api.get(URL, { params: { inicio, fim } });
  return z.array(agendamentoSchema).parse(data);
}

export async function criarAgendamento(dados: AgendamentoEntrada): Promise<Agendamento> {
  const { data } = await api.post(URL, dados);
  return agendamentoSchema.parse(data);
}

export async function atualizarAgendamento(
  id: number,
  dados: Partial<AgendamentoEntrada> & { situacao?: SituacaoAgenda; numero_os?: string },
): Promise<Agendamento> {
  const { data } = await api.put(`${URL}/${id}`, dados);
  return agendamentoSchema.parse(data);
}

export async function excluirAgendamento(id: number): Promise<void> {
  await api.delete(`${URL}/${id}`);
}
