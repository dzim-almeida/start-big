/**
 * @fileoverview Presets de fábrica (docs/etiquetas-plano.md, decisão D4).
 *
 * Ficam no CÓDIGO, não no banco: um preset novo ou corrigido chega na próxima
 * atualização, sem migração de dados. O lojista parte de um deles e salva a
 * sua variação como modelo da loja.
 *
 * Geometria das folhas: as Pimaco 6180–6183 (Carta) são compatíveis com as
 * Avery 5160–5163, e as margens batem com a tabela de parâmetros da Pimaco.
 * As A4 seguem a geometria das Avery L7160/L7163/L7651, que a Pimaco espelha
 * nos tamanhos. Medida de etiqueta varia de fabricante para fabricante: o
 * preset é ponto de partida — o "Imprimir teste" existe para conferir.
 */

import { gerarElementos, type OpcoesLayoutAuto } from './layoutAuto';
import type { ModeloEtiqueta, PaginaEtiqueta } from './modelo';

const CARTA = { largura_mm: 215.9, altura_mm: 279.4 };
const A4 = { largura_mm: 210, altura_mm: 297 };

const PADRAO: OpcoesLayoutAuto = { blocos: ['nome', 'preco_varejo', 'barras'] };

function bobina(largura: number, altura: number, extra: Partial<PaginaEtiqueta> = {}): PaginaEtiqueta {
  return {
    tipo: 'bobina',
    largura_mm: largura,
    altura_mm: altura,
    colunas: 1,
    espaco_colunas_mm: 0,
    espaco_linhas_mm: 0,
    margem_esq_mm: 0,
    margem_topo_mm: 0,
    folha: null,
    ...extra,
  };
}

function folha(
  papel: { largura_mm: number; altura_mm: number },
  etiqueta: { largura: number; altura: number; colunas: number; linhas: number },
  margem: { topo: number; esquerda: number; passoHorizontal: number },
): PaginaEtiqueta {
  return {
    tipo: 'folha',
    largura_mm: etiqueta.largura,
    altura_mm: etiqueta.altura,
    colunas: etiqueta.colunas,
    espaco_colunas_mm: Math.round((margem.passoHorizontal - etiqueta.largura) * 100) / 100,
    espaco_linhas_mm: 0,
    margem_esq_mm: margem.esquerda,
    margem_topo_mm: margem.topo,
    folha: { ...papel, linhas: etiqueta.linhas },
  };
}

function preset(slug: string, nome: string, descricao: string, pagina: PaginaEtiqueta, opcoes = PADRAO): ModeloEtiqueta {
  return {
    chave: `preset:${slug}`,
    nome,
    descricao,
    fonte: 'produto',
    id: null,
    definicao: { pagina, elementos: gerarElementos(pagina, opcoes), layout_auto: opcoes },
  };
}

export const PRESETS: ModeloEtiqueta[] = [
  // --- Rolos de térmica ---
  preset('rolo-40x25', 'Rolo 40 × 25 mm', 'Térmica, 1 coluna', bobina(40, 25)),
  preset('rolo-50x30', 'Rolo 50 × 30 mm', 'Térmica, 1 coluna', bobina(50, 30)),
  preset('rolo-60x40', 'Rolo 60 × 40 mm', 'Térmica, 1 coluna', bobina(60, 40), {
    blocos: ['nome', 'preco_varejo', 'barras', 'codigo_produto'],
  }),
  preset(
    'rolo-33x22-3col',
    'Rolo 33 × 22 mm (3 colunas)',
    'Térmica, rolo de 3 colunas — muito usado em joalheria e bijuteria',
    bobina(33, 22, { colunas: 3, espaco_colunas_mm: 2.5, margem_esq_mm: 1.5 }),
  ),
  preset('gondola-100x30', 'Gôndola 100 × 30 mm', 'Térmica, preço em destaque', bobina(100, 30), {
    blocos: ['nome', 'preco_varejo', 'codigo_produto', 'barras'],
  }),

  // --- Folhas adesivas (impressora comum) ---
  preset(
    'pimaco-6180',
    'Pimaco 6180 — Carta',
    '30 por folha · 66,7 × 25,4 mm',
    folha(CARTA, { largura: 66.7, altura: 25.4, colunas: 3, linhas: 10 }, { topo: 12.7, esquerda: 4.8, passoHorizontal: 69.9 }),
  ),
  preset(
    'pimaco-6181',
    'Pimaco 6181 — Carta',
    '20 por folha · 101,6 × 25,4 mm',
    folha(CARTA, { largura: 101.6, altura: 25.4, colunas: 2, linhas: 10 }, { topo: 12.7, esquerda: 4, passoHorizontal: 106.4 }),
  ),
  preset(
    'pimaco-6182',
    'Pimaco 6182 — Carta',
    '14 por folha · 101,6 × 33,9 mm',
    folha(CARTA, { largura: 101.6, altura: 33.9, colunas: 2, linhas: 7 }, { topo: 21.2, esquerda: 4, passoHorizontal: 106.4 }),
  ),
  preset(
    'pimaco-6183',
    'Pimaco 6183 — Carta',
    '10 por folha · 101,6 × 50,8 mm',
    folha(CARTA, { largura: 101.6, altura: 50.8, colunas: 2, linhas: 5 }, { topo: 12.7, esquerda: 4.1, passoHorizontal: 106.4 }),
    { blocos: ['nome', 'marca', 'preco_varejo', 'barras', 'codigo_produto'] },
  ),
  preset(
    'a4-65-38x21',
    'Folha A4 — 65 etiquetas',
    '38,1 × 21,2 mm (ex.: Pimaco A4251)',
    folha(A4, { largura: 38.1, altura: 21.2, colunas: 5, linhas: 13 }, { topo: 10.7, esquerda: 4.75, passoHorizontal: 40.64 }),
    { blocos: ['nome', 'barras'] },
  ),
  preset(
    'a4-21-63x38',
    'Folha A4 — 21 etiquetas',
    '63,5 × 38,1 mm (ex.: Pimaco A4256)',
    folha(A4, { largura: 63.5, altura: 38.1, colunas: 3, linhas: 7 }, { topo: 15.15, esquerda: 7.2, passoHorizontal: 66.04 }),
  ),
  preset(
    'a4-14-99x38',
    'Folha A4 — 14 etiquetas',
    '99,1 × 38,1 mm (ex.: Pimaco A4263)',
    folha(A4, { largura: 99.1, altura: 38.1, colunas: 2, linhas: 7 }, { topo: 15.15, esquerda: 4.65, passoHorizontal: 101.6 }),
  ),
];

export const PRESET_PADRAO = PRESETS[1];
