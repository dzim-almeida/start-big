/**
 * @fileoverview API service das etiquetas de envio (/etiquetas/envio)
 */

import api from '@/api/axios';
import type { DadosEnvio, OrigemEnvioItem, ParteEnvio, TipoOrigemEnvio } from '@/shared/etiquetas/envio';

const BASE_URL = 'etiquetas/envio' as const;

export async function buscarOrigensEnvio(busca?: string): Promise<OrigemEnvioItem[]> {
  const { data } = await api.get<OrigemEnvioItem[]>(`${BASE_URL}/origens`, { params: busca ? { busca } : {} });
  return data;
}

export async function getDadosEnvio(tipo: TipoOrigemEnvio, id: number): Promise<DadosEnvio> {
  const { data } = await api.get<DadosEnvio>(`${BASE_URL}/${tipo}/${id}`);
  return data;
}

export async function getRemetenteEnvio(): Promise<ParteEnvio> {
  const { data } = await api.get<ParteEnvio>(`${BASE_URL}/remetente`);
  return data;
}
