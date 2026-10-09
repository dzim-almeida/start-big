/**
 * @fileoverview Chamadas dos móveis terceirizados (Spec 11A §6). Toda escrita
 * devolve a seção da OS atualizada (o "pedir" devolve também o pedido criado).
 */
import api from '@/api/axios';

import {
  listaTerceirizadosSchema,
  pedirRespostaSchema,
  terceirizadosSchema,
  type ItemListaTerceirizados,
  type PedirResposta,
  type SituacaoTerceirizado,
  type TerceirizadosDaOS,
} from '../schemas/terceirizado.schema';

const URL_MARCENARIA = '/marcenaria';
const urlDaOS = (numeroOs: string) => `${URL_MARCENARIA}/os/${encodeURIComponent(numeroOs)}/terceirizados`;

export async function getTerceirizados(numeroOs: string): Promise<TerceirizadosDaOS> {
  const { data } = await api.get(urlDaOS(numeroOs));
  return terceirizadosSchema.parse(data);
}

async function escrever(numeroOs: string, caminho: string, corpo: object = {}): Promise<TerceirizadosDaOS> {
  const { data } = await api.post(`${urlDaOS(numeroOs)}${caminho}`, corpo);
  return terceirizadosSchema.parse(data);
}

/** Com o Compras: UM pedido de serviço em rascunho para os móveis (mesma central, 11A D9). */
export async function pedir(
  numeroOs: string, movelIds: number[], previsaoEntrega: string | null, observacao: string | null,
): Promise<PedirResposta> {
  const { data } = await api.post(`${urlDaOS(numeroOs)}/pedir`, {
    movel_ids: movelIds, previsao_entrega: previsaoEntrega, observacao,
  });
  return pedirRespostaSchema.parse(data);
}

/** Sem o Compras: o pedido anotado (número e previsão opcionais, 11A D3). */
export const enviarManual = (numeroOs: string, movelIds: number[], pedido: string | null, previsao: string | null) =>
  escrever(numeroOs, '/enviar-manual', { movel_ids: movelIds, pedido, previsao });

/** Sem o Compras: a chegada (padrão: hoje). */
export const receberManual = (numeroOs: string, movelIds: number[], data: string | null) =>
  escrever(numeroOs, '/receber-manual', { movel_ids: movelIds, data });

export const conferir = (numeroOs: string, movelIds: number[]) => escrever(numeroOs, '/conferir', { movel_ids: movelIds });
export const registrarProblema = (numeroOs: string, movelId: number, texto: string) =>
  escrever(numeroOs, `/${movelId}/problema`, { texto });
export const voltar = (numeroOs: string, movelId: number) => escrever(numeroOs, `/${movelId}/voltar`);

/** A lista geral das OS abertas (aba "Terceirizados" em Serviços, 11B D11). */
export async function getTerceirizadosEmAberto(filtros: {
  situacao?: SituacaoTerceirizado | null; atrasados?: boolean;
}): Promise<ItemListaTerceirizados[]> {
  const params: Record<string, string> = {};
  if (filtros.situacao) params.situacao = filtros.situacao;
  if (filtros.atrasados) params.atrasados = 'true';
  const { data } = await api.get(`${URL_MARCENARIA}/terceirizados`, { params });
  return listaTerceirizadosSchema.parse(data).itens;
}
