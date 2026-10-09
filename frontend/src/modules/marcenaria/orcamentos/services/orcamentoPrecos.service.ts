/**
 * @fileoverview Preços desatualizados e atualização com aviso (Spec 06A §6.5, O3).
 * As duas chamadas exigem `view_custos_marcenaria`.
 */
import api from '@/api/axios';

import {
  orcamentoDetalheSchema,
  precosDesatualizadosSchema,
  type OrcamentoDetalhe,
  type PrecosDesatualizados,
} from '../schemas/orcamentoDetalhe.schema';
import { URL_ORCAMENTOS } from './orcamento.service';

/** Insumos com custo ou "sofre perda" diferentes do produto hoje, e o efeito no total. */
export async function getPrecosDesatualizados(id: number): Promise<PrecosDesatualizados> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/${id}/precos-desatualizados`);
  return precosDesatualizadosSchema.parse(data);
}

/** Grava os custos de hoje nos insumos escolhidos (só em rascunho). */
export async function atualizarPrecos(id: number, revisao: number, insumoIds: number[]): Promise<OrcamentoDetalhe> {
  const { data } = await api.post(
    `${URL_ORCAMENTOS}/${id}/atualizar-precos`,
    { insumo_ids: insumoIds },
    { params: { revisao } },
  );
  return orcamentoDetalheSchema.parse(data);
}
