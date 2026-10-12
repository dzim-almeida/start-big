/**
 * @fileoverview Chamadas da aprovação do orçamento (Spec 08A §6).
 * Aprovar e desfazer mandam a revisão (trava otimista) e devolvem o detalhe.
 */
import api from '@/api/axios';

import {
  resumoPorOsSchema,
  simulacaoAprovacaoSchema,
  type AprovacaoEntrada,
  type DesfazerEntrada,
  type ResumoPorOs,
  type SimulacaoAprovacao,
} from '../schemas/aprovacao.schema';
import { orcamentoDetalheSchema, type OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { URL_ORCAMENTOS } from './orcamento.service';

/** Os números do que SERIA aprovado (não grava nada, sem revisão). */
export async function simularAprovacao(id: number, entrada: AprovacaoEntrada): Promise<SimulacaoAprovacao> {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/aprovacao/simular`, entrada);
  return simulacaoAprovacaoSchema.parse(data);
}

/** Aprova (todo ou em parte) e cria a OS; devolve o detalhe com `os` preenchido. */
export async function aprovarOrcamento(id: number, revisao: number, entrada: AprovacaoEntrada): Promise<OrcamentoDetalhe> {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/aprovar`, entrada, { params: { revisao } });
  return orcamentoDetalheSchema.parse(data);
}

/** Cancela a OS e volta o orçamento para ENVIADO (08A D20). */
export async function desfazerAprovacao(id: number, revisao: number, entrada: DesfazerEntrada): Promise<OrcamentoDetalhe> {
  const { data } = await api.post(`${URL_ORCAMENTOS}/${id}/desfazer-aprovacao`, entrada, { params: { revisao } });
  return orcamentoDetalheSchema.parse(data);
}

/** O orçamento que gerou a OS (aba "Orçamento" da OS). 404 = OS sem orçamento. */
export async function getResumoPorOs(numeroOs: string): Promise<ResumoPorOs> {
  const { data } = await api.get(`${URL_ORCAMENTOS}/por-os/${encodeURIComponent(numeroOs)}`);
  return resumoPorOsSchema.parse(data);
}
