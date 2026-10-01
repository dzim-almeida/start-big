import api from '@/api/axios';
import { safeParseResponse } from '@/shared/utils/parse.utils';
import {
  RelatorioFaturamentoSchema,
  type RelatorioFaturamento,
} from './schemas/faturamento.schema';
import { RelatorioRankingSchema, type RelatorioRanking } from './schemas/ranking.schema';
import { RelatorioComissaoSchema, type RelatorioComissao } from './schemas/comissao.schema';
import { RelatorioEstoqueSchema, type RelatorioEstoque } from './schemas/estoque.schema';
import {
  RelatorioOSPerformanceSchema,
  type RelatorioOSPerformance,
} from './schemas/osPerformance.schema';
import {
  RelatorioExtratoFuncionarioSchema,
  type RelatorioExtratoFuncionario,
} from './schemas/extratoFuncionario.schema';
import {
  RelatorioRegrasPrecoSchema,
  type RelatorioRegrasPreco,
} from './schemas/regrasPreco.schema';
import { RelatorioContadorSchema, type RelatorioContador } from './schemas/contador.schema';

/**
 * Faturamento (vendas + OS finalizadas) no intervalo [inicio, fim].
 * Datas em formato YYYY-MM-DD.
 */
export async function getFaturamento(inicio: string, fim: string): Promise<RelatorioFaturamento> {
  const { data } = await api.get('/relatorios/faturamento', { params: { inicio, fim } });
  return safeParseResponse(RelatorioFaturamentoSchema, data, 'getFaturamento');
}

/** Ranking de funcionários por faturamento (vendas + OS) no intervalo. */
export async function getRanking(inicio: string, fim: string): Promise<RelatorioRanking> {
  const { data } = await api.get('/relatorios/ranking-funcionarios', { params: { inicio, fim } });
  return safeParseResponse(RelatorioRankingSchema, data, 'getRanking');
}

/** Comissão apurada por funcionário no intervalo (cascata funcionário→cargo). */
export async function getComissao(inicio: string, fim: string): Promise<RelatorioComissao> {
  const { data } = await api.get('/relatorios/comissoes', { params: { inicio, fim } });
  return safeParseResponse(RelatorioComissaoSchema, data, 'getComissao');
}

/** Estoque + Curva ABC (por faturamento no intervalo) + reposição + parados. */
export async function getEstoque(inicio: string, fim: string): Promise<RelatorioEstoque> {
  const { data } = await api.get('/relatorios/estoque', { params: { inicio, fim } });
  return safeParseResponse(RelatorioEstoqueSchema, data, 'getEstoque');
}

/** Desempenho de OS no intervalo: throughput, tempo, reparo e por técnico. */
export async function getOSPerformance(
  inicio: string,
  fim: string,
): Promise<RelatorioOSPerformance> {
  const { data } = await api.get('/relatorios/os-performance', { params: { inicio, fim } });
  return safeParseResponse(RelatorioOSPerformanceSchema, data, 'getOSPerformance');
}

/** Vendas com regra de preço por quantidade (R1/R2/R3): o que venderam e o que abateram. */
export async function getRegrasPreco(inicio: string, fim: string): Promise<RelatorioRegrasPreco> {
  const { data } = await api.get('/relatorios/regras-preco', { params: { inicio, fim } });
  return safeParseResponse(RelatorioRegrasPrecoSchema, data, 'getRegrasPreco');
}

/** Receita do período separada como o contador declara no PGDAS-D. */
export async function getContador(inicio: string, fim: string): Promise<RelatorioContador> {
  const { data } = await api.get('/relatorios/contador', { params: { inicio, fim } });
  return safeParseResponse(RelatorioContadorSchema, data, 'getContador');
}

/**
 * Os serviços que uma pessoa executou nas OS finalizadas do intervalo.
 *
 * É o papel que o dono imprime e entrega. Peça não entra — material é custo da
 * loja, não produção do técnico.
 */
export async function getExtratoFuncionario(
  funcionarioId: number,
  inicio: string,
  fim: string,
): Promise<RelatorioExtratoFuncionario> {
  const { data } = await api.get('/relatorios/extrato-funcionario', {
    params: { funcionario_id: funcionarioId, inicio, fim },
  });
  return safeParseResponse(RelatorioExtratoFuncionarioSchema, data, 'getExtratoFuncionario');
}
