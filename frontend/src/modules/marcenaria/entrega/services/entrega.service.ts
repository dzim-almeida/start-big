/**
 * @fileoverview Chamadas da entrega da OS (Spec 13A §6). Toda escrita devolve
 * a aba atualizada, com os `avisos` da ação (ex.: sem a foto do termo).
 */
import api from '@/api/axios';

import { entregaDaOSSchema, resumoSchema, type EntregaDaOS, type Marcacao, type ResumoEntrega } from '../schemas/entrega.schema';

export const URL_MARCENARIA = '/marcenaria';
/** A base das rotas de uma OS (o número vai codificado: tem hífen, mas nunca se sabe). */
export const urlDaOS = (numeroOs: string) => `${URL_MARCENARIA}/os/${encodeURIComponent(numeroOs)}`;
const urlEntrega = (numeroOs: string) => `${urlDaOS(numeroOs)}/entrega`;

/** Lê a resposta de qualquer escrita (a aba inteira). */
export const lerResposta = (data: unknown): EntregaDaOS => entregaDaOSSchema.parse(data);

export async function getEntrega(numeroOs: string): Promise<EntregaDaOS> {
  const { data } = await api.get(urlEntrega(numeroOs));
  return lerResposta(data);
}

/** Para o aviso da finalização (13B D18): o que falta entregar e as pendências. */
export async function getResumo(numeroOs: string): Promise<ResumoEntrega> {
  const { data } = await api.get(`${urlEntrega(numeroOs)}/resumo`);
  return resumoSchema.parse(data);
}

export async function editarChecklist(numeroOs: string, entregaId: number, itens: string[]): Promise<EntregaDaOS> {
  const { data } = await api.put(`${urlEntrega(numeroOs)}/${entregaId}/checklist`, { itens });
  return lerResposta(data);
}

/** O que vai no registro (13A §6.2). `checklist: null` = não mexe nas marcações. */
export interface RegistroEntrega {
  situacao: 'CONFORME' | 'COM_RESSALVAS';
  data_entrega: string | null;
  montadores: number[];
  recebido_por: string | null;
  checklist: Marcacao[] | null;
  observacoes: string | null;
  pendencias: string[];
}

export async function registrar(numeroOs: string, entregaId: number, registro: RegistroEntrega): Promise<EntregaDaOS> {
  const { data } = await api.post(`${urlEntrega(numeroOs)}/${entregaId}/registrar`, registro);
  return lerResposta(data);
}

export async function criarPendencia(numeroOs: string, entregaId: number, descricao: string): Promise<EntregaDaOS> {
  const { data } = await api.post(`${urlEntrega(numeroOs)}/${entregaId}/pendencias`, { descricao });
  return lerResposta(data);
}

export async function resolverPendencia(
  numeroOs: string, entregaId: number, pendenciaId: number, resolucao: string, dataResolucao: string | null,
): Promise<EntregaDaOS> {
  const { data } = await api.post(`${urlEntrega(numeroOs)}/${entregaId}/pendencias/${pendenciaId}/resolver`, {
    resolucao, data: dataResolucao,
  });
  return lerResposta(data);
}

export async function reabrirPendencia(numeroOs: string, entregaId: number, pendenciaId: number): Promise<EntregaDaOS> {
  const { data } = await api.post(`${urlEntrega(numeroOs)}/${entregaId}/pendencias/${pendenciaId}/reabrir`);
  return lerResposta(data);
}

/** A foto vai para a galeria da OS e fica ligada à entrega (13A D7). */
export async function enviarFoto(
  numeroOs: string, entregaId: number, tipo: 'TERMO' | 'MONTAGEM', arquivo: File,
): Promise<EntregaDaOS> {
  const corpo = new FormData();
  corpo.append('tipo', tipo);
  corpo.append('arquivo', arquivo);
  // Multipart como o upload de fotos da OS (o navegador completa o "boundary").
  const { data } = await api.post(`${urlEntrega(numeroOs)}/${entregaId}/fotos`, corpo, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return lerResposta(data);
}

/** Excluir pela entrega tira a foto também da galeria da OS (13A D7). */
export async function excluirFoto(numeroOs: string, entregaId: number, fotoId: number): Promise<EntregaDaOS> {
  const { data } = await api.delete(`${urlEntrega(numeroOs)}/${entregaId}/fotos/${fotoId}`);
  return lerResposta(data);
}
