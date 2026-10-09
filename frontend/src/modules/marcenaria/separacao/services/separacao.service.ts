/**
 * @fileoverview Chamadas da separação de material da OS (Spec 10A §6.1).
 *
 * Toda escrita manda `separada_esperada_milesimos` (o retirado que a tela
 * mostrava, 10A D16) e devolve a SEPARAÇÃO INTEIRA atualizada.
 */
import api from '@/api/axios';

import {
  disponivelSchema,
  faltasSchema,
  leituraSchema,
  separacaoSchema,
  type Disponivel,
  type FaltasDaOS,
  type Leitura,
  type Separacao,
} from '../schemas/separacao.schema';

const URL_MARCENARIA = '/marcenaria';

/** O número da OS vai no caminho ("OS-2026-000512"): sempre codificado. */
const urlDaOS = (numeroOs: string) => `${URL_MARCENARIA}/os/${encodeURIComponent(numeroOs)}/separacao`;

export async function getSeparacao(numeroOs: string): Promise<Separacao> {
  const { data } = await api.get(urlDaOS(numeroOs));
  return separacaoSchema.parse(data);
}

/** Retirar (10A D6) ou devolver (D9): quanto, com a trava da linha. */
async function movimentar(
  acao: 'retirar' | 'devolver', numeroOs: string, itemId: number, quantidadeMilesimos: number, separadaEsperada: number,
): Promise<Separacao> {
  const { data } = await api.post(`${urlDaOS(numeroOs)}/${itemId}/${acao}`, {
    quantidade_milesimos: quantidadeMilesimos,
    separada_esperada_milesimos: separadaEsperada,
  });
  return separacaoSchema.parse(data);
}

/** Concluir (usou menos / não usado, D10-D11) ou reabrir (D12): só a trava. */
async function conferir(acao: 'concluir' | 'reabrir', numeroOs: string, itemId: number, separadaEsperada: number) {
  const { data } = await api.post(`${urlDaOS(numeroOs)}/${itemId}/${acao}`, {
    separada_esperada_milesimos: separadaEsperada,
  });
  return separacaoSchema.parse(data);
}

export const retirar = (numeroOs: string, itemId: number, quantidade: number, separadaEsperada: number) =>
  movimentar('retirar', numeroOs, itemId, quantidade, separadaEsperada);
export const devolver = (numeroOs: string, itemId: number, quantidade: number, separadaEsperada: number) =>
  movimentar('devolver', numeroOs, itemId, quantidade, separadaEsperada);
export const concluir = (numeroOs: string, itemId: number, separadaEsperada: number) =>
  conferir('concluir', numeroOs, itemId, separadaEsperada);
export const reabrir = (numeroOs: string, itemId: number, separadaEsperada: number) =>
  conferir('reabrir', numeroOs, itemId, separadaEsperada);

/** Leitor (10A D20): a linha do código lido; 404 = "não faz parte desta OS". */
export async function lerCodigo(numeroOs: string, codigo: string): Promise<Leitura> {
  const { data } = await api.get(`${urlDaOS(numeroOs)}/ler`, { params: { codigo } });
  return leituraSchema.parse(data);
}

export async function getFaltas(numeroOs: string): Promise<FaltasDaOS> {
  const { data } = await api.get(`${urlDaOS(numeroOs)}/faltas`);
  return faltasSchema.parse(data);
}

/** Disponível na busca de insumo do orçamento (10A D19). Lista vazia não chama. */
export async function getDisponivel(produtoIds: number[]): Promise<Disponivel> {
  if (!produtoIds.length) return {};
  const { data } = await api.get(`${URL_MARCENARIA}/estoque/disponivel`, { params: { produto_ids: produtoIds.join(',') } });
  return disponivelSchema.parse(data);
}
