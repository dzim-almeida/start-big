/**
 * @fileoverview O orçamento enquanto é digitado: a árvore na forma da TELA
 * (reais, m², metros) e as conversões de ida e volta para a forma do
 * SERVIDOR (centavos, mm², mm). Funções puras — o componente só guarda o
 * estado e chama estas.
 */

import type {
  AmbienteEscrita,
  InsumoBusca,
  OrcamentoEscrita,
  OrcamentoRead,
  UnidadeConsumo,
} from '../types/fabrica.types';
import {
  bpParaPercentual,
  consumoParaInteiro,
  consumoParaTela,
  custoDoMaterial,
  percentualParaBp,
} from './calculo';

export interface MaterialEdit {
  chave: number;
  /** Id da linha gravada: com ele, o servidor mantém o custo copiado na inclusão. */
  id: number | null;
  produto_id: number;
  descricao: string;
  unidade_consumo: UnidadeConsumo;
  consumo_por_unidade: number;
  sofre_perda: boolean;
  unidade_medida: string | null;
  custo_unitario: number;
  /** Na unidade da tela: m², metros ou unidades. */
  quantidade: number | null;
}

export interface MovelEdit {
  chave: number;
  nome: string;
  largura_mm: number | null;
  altura_mm: number | null;
  profundidade_mm: number | null;
  precoReais: number | undefined;
  terceirizado: boolean;
  custoTerceiroReais: number | undefined;
  materiais: MaterialEdit[];
}

export interface AmbienteEdit {
  chave: number;
  nome: string;
  moveis: MovelEdit[];
}

export interface OrcamentoEdit {
  perdaPercentual: number | null;
  sinalPercentual: number | null;
  validade: string | null;
  observacao: string;
  ambientes: AmbienteEdit[];
}

let proximaChave = 1;
const chave = () => proximaChave++;

const paraReais = (centavos: number | null | undefined) => (centavos != null ? centavos / 100 : undefined);
const paraCentavos = (reais: number | undefined | null) => (reais != null ? Math.round(reais * 100) : 0);
const medida = (v: number | null | undefined) => (v && v > 0 ? Math.round(v) : null);

// --- Servidor → tela ------------------------------------------------------------

export function editavelDe(orc: OrcamentoRead): OrcamentoEdit {
  return {
    perdaPercentual: bpParaPercentual(orc.perda_bp),
    sinalPercentual: bpParaPercentual(orc.sinal_bp),
    validade: orc.validade,
    observacao: orc.observacao ?? '',
    ambientes: orc.ambientes.map((amb) => ({
      chave: chave(),
      nome: amb.nome,
      moveis: amb.moveis.map((mov) => ({
        chave: chave(),
        nome: mov.nome,
        largura_mm: mov.largura_mm,
        altura_mm: mov.altura_mm,
        profundidade_mm: mov.profundidade_mm,
        precoReais: paraReais(mov.preco_venda),
        terceirizado: mov.terceirizado,
        custoTerceiroReais: paraReais(mov.custo_terceiro),
        materiais: mov.materiais
          // Material cujo produto deixou de ser insumo não tem como ser
          // convertido; o servidor recusa e a mensagem diz qual é.
          .filter((m) => m.produto_id != null && m.unidade_consumo && m.consumo_por_unidade)
          .map((m) => ({
            chave: chave(),
            id: m.id,
            produto_id: m.produto_id as number,
            descricao: m.descricao,
            unidade_consumo: m.unidade_consumo as UnidadeConsumo,
            consumo_por_unidade: m.consumo_por_unidade as number,
            sofre_perda: m.sofre_perda,
            unidade_medida: m.unidade_medida,
            custo_unitario: m.custo_unitario ?? 0,
            quantidade: consumoParaTela(m.unidade_consumo as UnidadeConsumo, m.consumo),
          })),
      })),
    })),
  };
}

// --- Tela → servidor --------------------------------------------------------------

export function escritaDe(edit: OrcamentoEdit): OrcamentoEscrita {
  return {
    perda_bp: percentualParaBp(edit.perdaPercentual),
    sinal_bp: percentualParaBp(edit.sinalPercentual),
    validade: edit.validade || null,
    observacao: edit.observacao.trim() || null,
    ambientes: edit.ambientes.map<AmbienteEscrita>((amb) => ({
      nome: amb.nome.trim(),
      moveis: amb.moveis.map((mov) => ({
        nome: mov.nome.trim(),
        largura_mm: medida(mov.largura_mm),
        altura_mm: medida(mov.altura_mm),
        profundidade_mm: medida(mov.profundidade_mm),
        preco_venda: paraCentavos(mov.precoReais),
        terceirizado: mov.terceirizado,
        custo_terceiro: mov.terceirizado ? paraCentavos(mov.custoTerceiroReais) : null,
        materiais: mov.materiais.map((m) => ({
          id: m.id,
          produto_id: m.produto_id,
          consumo: consumoParaInteiro(m.unidade_consumo, m.quantidade) ?? 0,
        })),
      })),
    })),
  };
}

// --- Novas linhas --------------------------------------------------------------------

export function novoAmbiente(nome = ''): AmbienteEdit {
  return { chave: chave(), nome, moveis: [novoMovel()] };
}

export function novoMovel(): MovelEdit {
  return {
    chave: chave(), nome: '', largura_mm: null, altura_mm: null, profundidade_mm: null,
    precoReais: undefined, terceirizado: false, custoTerceiroReais: undefined, materiais: [],
  };
}

export function materialDe(insumo: InsumoBusca): MaterialEdit {
  return {
    chave: chave(),
    id: null,
    produto_id: insumo.id,
    descricao: insumo.nome,
    unidade_consumo: insumo.unidade_consumo,
    consumo_por_unidade: insumo.consumo_por_unidade,
    sofre_perda: insumo.sofre_perda,
    unidade_medida: insumo.unidade_medida,
    custo_unitario: insumo.custo_unitario ?? 0,
    quantidade: null,
  };
}

// --- Prévia (o servidor recalcula ao salvar) -----------------------------------------------

export function custoMaterial(m: MaterialEdit, perdaPercentual: number | null): number {
  const consumo = consumoParaInteiro(m.unidade_consumo, m.quantidade);
  if (!consumo) return 0;
  return custoDoMaterial(consumo, percentualParaBp(perdaPercentual), m.sofre_perda, m.consumo_por_unidade, m.custo_unitario);
}

export function custoMovel(mov: MovelEdit, perdaPercentual: number | null): number {
  const materiais = mov.materiais.reduce((s, m) => s + custoMaterial(m, perdaPercentual), 0);
  return materiais + (mov.terceirizado ? paraCentavos(mov.custoTerceiroReais) : 0);
}

export interface Totais {
  total: number;
  custo: number;
  /** Margem sobre o preço, em pontos-base; null sem preço. */
  margemBp: number | null;
  sinal: number;
}

export function totaisDe(edit: OrcamentoEdit): Totais {
  const moveis = edit.ambientes.flatMap((a) => a.moveis);
  const total = moveis.reduce((s, m) => s + paraCentavos(m.precoReais), 0);
  const custo = moveis.reduce((s, m) => s + custoMovel(m, edit.perdaPercentual), 0);
  return {
    total,
    custo,
    margemBp: total > 0 ? Math.round(((total - custo) * 10_000) / total) : null,
    sinal: Math.ceil((total * percentualParaBp(edit.sinalPercentual)) / 10_000),
  };
}

/** Preço sugerido: custo × (1 + margem padrão de Produtos), em reais. */
export function precoSugerido(custoCentavos: number, margemPercentual: number): number | null {
  if (custoCentavos <= 0) return null;
  return Math.round(custoCentavos * (1 + margemPercentual / 100)) / 100;
}

/** O que impede de salvar, em português de gente. Vazio = pode salvar. */
export function problemasDe(edit: OrcamentoEdit): string[] {
  const lista: string[] = [];
  const perda = edit.perdaPercentual ?? 0;
  if (perda < 0 || perda > 50) lista.push('A perda vai de 0% a 50%.');
  const sinal = edit.sinalPercentual ?? 0;
  if (sinal < 0 || sinal > 100) lista.push('O sinal vai de 0% a 100%.');
  edit.ambientes.forEach((amb, i) => {
    const nomeAmb = amb.nome.trim() || `Ambiente ${i + 1}`;
    if (!amb.nome.trim()) lista.push(`${nomeAmb}: dê um nome ao ambiente.`);
    amb.moveis.forEach((mov, j) => {
      const nomeMov = `${nomeAmb} — ${mov.nome.trim() || `móvel ${j + 1}`}`;
      if (!mov.nome.trim()) lista.push(`${nomeMov}: dê um nome ao móvel.`);
      mov.materiais.forEach((m) => {
        if (!consumoParaInteiro(m.unidade_consumo, m.quantidade)) {
          lista.push(`${nomeMov}: informe quanto de "${m.descricao}" vai.`);
        }
      });
    });
  });
  return lista;
}
