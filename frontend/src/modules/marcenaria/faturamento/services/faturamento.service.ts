/**
 * @fileoverview Chamadas do faturamento dos móveis de uma OS
 * (docs/marcenaria-faturamento-plano.md, F3/F4).
 */
import api from '@/api/axios';

import { urlDaOS } from '@/modules/marcenaria/entrega/services/entrega.service';
import {
  emissaoSchema,
  faturamentoDaOSSchema,
  previaNotaSchema,
  type FaturamentoDaOS,
  type PreviaNota,
  type ResultadoEmissao,
} from '../schemas/faturamento.schema';

const urlFaturamento = (numeroOs: string) => `${urlDaOS(numeroOs)}/faturamento`;

export async function getFaturamento(numeroOs: string): Promise<FaturamentoDaOS> {
  const { data } = await api.get(urlFaturamento(numeroOs));
  return faturamentoDaOSSchema.parse(data);
}

/** Prévia da nota dos móveis escolhidos: não emite e não reserva número. */
export async function previaDaNota(numeroOs: string, movelIds: number[]): Promise<PreviaNota> {
  const { data } = await api.post(`${urlFaturamento(numeroOs)}/preview`, { movel_ids: movelIds });
  return previaNotaSchema.parse(data);
}

/** Emite a NF-e dos móveis escolhidos (uma entrega; na entrega futura, a remessa). */
export async function emitirNota(numeroOs: string, movelIds: number[]): Promise<ResultadoEmissao> {
  const { data } = await api.post(`${urlFaturamento(numeroOs)}/emitir`, { movel_ids: movelIds });
  return emissaoSchema.parse(data);
}

/** Entrega futura (F4): prévia da nota de simples faturamento (todos os móveis ainda sem ela). */
export async function previaDoSimplesFaturamento(numeroOs: string): Promise<PreviaNota> {
  const { data } = await api.post(`${urlFaturamento(numeroOs)}/simples-faturamento/preview`);
  return previaNotaSchema.parse(data);
}

/** Entrega futura (F4): emite a nota de simples faturamento (5922). */
export async function emitirSimplesFaturamento(numeroOs: string): Promise<ResultadoEmissao> {
  const { data } = await api.post(`${urlFaturamento(numeroOs)}/simples-faturamento/emitir`);
  return emissaoSchema.parse(data);
}
