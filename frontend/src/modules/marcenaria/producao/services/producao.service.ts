/**
 * @fileoverview Chamadas da produção (Spec 12A §6). Toda escrita devolve a
 * produção da OS atualizada, com a `sugestao_status` (o backend nunca muda o
 * status da OS sozinho).
 */
import api from '@/api/axios';

import { producaoSchema, quadroSchema, type ItemQuadro, type ProducaoDaOS } from '../schemas/producao.schema';

const URL_MARCENARIA = '/marcenaria';
const urlDaOS = (numeroOs: string) => `${URL_MARCENARIA}/os/${encodeURIComponent(numeroOs)}/producao`;

export async function getProducao(numeroOs: string): Promise<ProducaoDaOS> {
  const { data } = await api.get(urlDaOS(numeroOs));
  return producaoSchema.parse(data);
}

async function escrever(numeroOs: string, metodo: 'post' | 'put', caminho: string, corpo: object = {}): Promise<ProducaoDaOS> {
  const { data } = await api[metodo](`${urlDaOS(numeroOs)}${caminho}`, corpo);
  return producaoSchema.parse(data);
}

/**
 * O lote vai com quem fez (12A D7). `null` = não manda o campo, e o backend
 * usa o funcionário do usuário logado.
 */
const lote = (etapaIds: number[], responsavelId: number | null) =>
  (responsavelId ? { etapa_ids: etapaIds, responsavel_funcionario_id: responsavelId } : { etapa_ids: etapaIds });

/** PENDENTE → EM_EXECUCAO, com o responsável (as outras ficam como estão). */
export const iniciar = (numeroOs: string, etapaIds: number[], responsavelId: number | null) =>
  escrever(numeroOs, 'post', '/etapas/iniciar', lote(etapaIds, responsavelId));

/** Conclui as etapas (até de móveis diferentes). Concluir de novo não muda nada. */
export const concluir = (numeroOs: string, etapaIds: number[], responsavelId: number | null) =>
  escrever(numeroOs, 'post', '/etapas/concluir', lote(etapaIds, responsavelId));

/** Volta a etapa a PENDENTE (limpa datas e responsável; o histórico guarda). */
export const reabrir = (numeroOs: string, etapaId: number) => escrever(numeroOs, 'post', `/etapas/${etapaId}/reabrir`);

/** A lista inteira de etapas do móvel, na ordem nova (`id` = etapa que já existia). */
export const editarEtapas = (numeroOs: string, movelId: number, etapas: { id: number | null; nome: string }[]) =>
  escrever(numeroOs, 'put', `/moveis/${movelId}/etapas`, {
    etapas: etapas.map((e) => (e.id ? { id: e.id, nome: e.nome } : { nome: e.nome })),
  });

/** Móvel sem etapas ganha as etapas padrão da configuração (12A D6). */
export const aplicarPadrao = (numeroOs: string, movelId: number) =>
  escrever(numeroOs, 'post', `/moveis/${movelId}/aplicar-padrao`);

/** O quadro da fábrica: as OS abertas, já na ordem da previsão (12A D18). */
export async function getQuadro(): Promise<ItemQuadro[]> {
  const { data } = await api.get(`${URL_MARCENARIA}/producao`);
  return quadroSchema.parse(data).itens;
}
