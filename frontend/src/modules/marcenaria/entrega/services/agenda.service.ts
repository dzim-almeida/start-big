/**
 * @fileoverview Chamadas da agenda de instalação (Spec 13A D9-D13).
 */
import api from '@/api/axios';

import { instalacoesSchema, type EntregaDaOS, type Instalacao } from '../schemas/entrega.schema';
import { lerResposta, URL_MARCENARIA, urlDaOS } from './entrega.service';

/** A visita: data, hora (opcional), ambientes ainda não entregues e montadores. */
export interface AgendamentoEnvio {
  data: string;
  hora_inicio: string | null;
  ambiente_ids: number[];
  montadores: number[];
  observacao: string | null;
}

export async function agendar(numeroOs: string, agendamento: AgendamentoEnvio): Promise<EntregaDaOS> {
  const { data } = await api.post(`${urlDaOS(numeroOs)}/agendamentos`, agendamento);
  return lerResposta(data);
}

export async function editarAgendamento(numeroOs: string, id: number, agendamento: AgendamentoEnvio): Promise<EntregaDaOS> {
  const { data } = await api.put(`${urlDaOS(numeroOs)}/agendamentos/${id}`, agendamento);
  return lerResposta(data);
}

export async function excluirAgendamento(numeroOs: string, id: number): Promise<EntregaDaOS> {
  const { data } = await api.delete(`${urlDaOS(numeroOs)}/agendamentos/${id}`);
  return lerResposta(data);
}

/** A lista de instalações (aba "Instalações" em Serviços, 13B D16). */
export async function getInstalacoes(filtros: {
  de?: string | null; ate?: string | null; montadorId?: number | null; atrasadas?: boolean;
}): Promise<Instalacao[]> {
  const params: Record<string, string> = {};
  if (filtros.de) params.de = filtros.de;
  if (filtros.ate) params.ate = filtros.ate;
  if (filtros.montadorId) params.montador_id = String(filtros.montadorId);
  if (filtros.atrasadas) params.atrasadas = 'true';
  const { data } = await api.get(`${URL_MARCENARIA}/instalacoes`, { params });
  return instalacoesSchema.parse(data).itens;
}
