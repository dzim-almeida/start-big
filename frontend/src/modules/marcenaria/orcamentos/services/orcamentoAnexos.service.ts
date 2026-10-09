/**
 * @fileoverview Anexos da medição: fotos e PDFs (Spec 06A D27-D31).
 * Não mandam a revisão: anexo não mexe nela (D31), por isso nem passam pela
 * fila de escrita (06B D47).
 */
import api from '@/api/axios';

import { anexoSchema, type AnexoOrcamento } from '../schemas/orcamentoDetalhe.schema';
import { URL_ORCAMENTOS } from './orcamento.service';

export async function listarAnexos(id: number): Promise<AnexoOrcamento[]> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/${id}/anexos`);
  return anexoSchema.array().parse(data);
}

/** Envia um arquivo (multipart). O upload pode demorar mais que o timeout padrão. */
export async function incluirAnexo(id: number, arquivo: File, legenda?: string): Promise<AnexoOrcamento> {
  const form = new FormData();
  form.append('arquivo', arquivo);
  if (legenda) form.append('legenda', legenda);
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/anexos`, form, { timeout: 60_000 });
  return anexoSchema.parse(data);
}

export async function alterarLegenda(id: number, anexoId: number, legenda: string | null): Promise<AnexoOrcamento> {
  const { data } = await api.patch(`${URL_ORCAMENTOS}/${id}/anexos/${anexoId}`, { legenda });
  return anexoSchema.parse(data);
}

export async function removerAnexo(id: number, anexoId: number): Promise<void> {
  await api.delete(`${URL_ORCAMENTOS}/${id}/anexos/${anexoId}`);
}
