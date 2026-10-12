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
import { gerarDanfe, gerarMovel, gerarVolume } from './layoutEnvio';
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
    // Só o que COMPLEMENTA o resumo de papel da fila (tipo, medida, colunas).
    descricao: descricao || undefined,
    fonte: 'produto',
    id: null,
    definicao: { pagina, elementos: gerarElementos(pagina, opcoes), layout_auto: opcoes },
  };
}

export const PRESETS: ModeloEtiqueta[] = [
  // --- Rolos de térmica ---
  preset('rolo-40x25', 'Rolo 40 × 25 mm', '', bobina(40, 25)),
  preset('rolo-50x30', 'Rolo 50 × 30 mm', '', bobina(50, 30)),
  preset('rolo-60x40', 'Rolo 60 × 40 mm', '', bobina(60, 40), {
    blocos: ['nome', 'preco_varejo', 'barras', 'codigo_produto'],
  }),
  preset(
    'rolo-33x22-3col',
    'Rolo 33 × 22 mm (3 colunas)',
    'muito usado em joalheria e bijuteria',
    bobina(33, 22, { colunas: 3, espaco_colunas_mm: 2.5, margem_esq_mm: 1.5 }),
  ),
  preset('gondola-100x30', 'Gôndola 100 × 30 mm', 'preço em destaque', bobina(100, 30), {
    blocos: ['nome', 'preco_varejo', 'codigo_produto', 'barras'],
  }),

  // --- Folhas adesivas (impressora comum) ---
  preset(
    'pimaco-6180',
    'Pimaco 6180 — Carta',
    'folha tamanho Carta',
    folha(CARTA, { largura: 66.7, altura: 25.4, colunas: 3, linhas: 10 }, { topo: 12.7, esquerda: 4.8, passoHorizontal: 69.9 }),
  ),
  preset(
    'pimaco-6181',
    'Pimaco 6181 — Carta',
    'folha tamanho Carta',
    folha(CARTA, { largura: 101.6, altura: 25.4, colunas: 2, linhas: 10 }, { topo: 12.7, esquerda: 4, passoHorizontal: 106.4 }),
  ),
  preset(
    'pimaco-6182',
    'Pimaco 6182 — Carta',
    'folha tamanho Carta',
    folha(CARTA, { largura: 101.6, altura: 33.9, colunas: 2, linhas: 7 }, { topo: 21.2, esquerda: 4, passoHorizontal: 106.4 }),
  ),
  preset(
    'pimaco-6183',
    'Pimaco 6183 — Carta',
    'folha tamanho Carta',
    folha(CARTA, { largura: 101.6, altura: 50.8, colunas: 2, linhas: 5 }, { topo: 12.7, esquerda: 4.1, passoHorizontal: 106.4 }),
    { blocos: ['nome', 'marca', 'preco_varejo', 'barras', 'codigo_produto'] },
  ),
  preset(
    'a4-65-38x21',
    'Folha A4 — 65 etiquetas',
    'ex.: Pimaco A4251',
    folha(A4, { largura: 38.1, altura: 21.2, colunas: 5, linhas: 13 }, { topo: 10.7, esquerda: 4.75, passoHorizontal: 40.64 }),
    { blocos: ['nome', 'barras'] },
  ),
  preset(
    'a4-21-63x38',
    'Folha A4 — 21 etiquetas',
    'ex.: Pimaco A4256',
    folha(A4, { largura: 63.5, altura: 38.1, colunas: 3, linhas: 7 }, { topo: 15.15, esquerda: 7.2, passoHorizontal: 66.04 }),
  ),
  preset(
    'a4-14-99x38',
    'Folha A4 — 14 etiquetas',
    'ex.: Pimaco A4263',
    folha(A4, { largura: 99.1, altura: 38.1, colunas: 2, linhas: 7 }, { topo: 15.15, esquerda: 4.65, passoHorizontal: 101.6 }),
  ),
];

export const PRESET_PADRAO = PRESETS[1];

// --- Envio (fase 5) ---

function presetEnvio(
  slug: string,
  nome: string,
  descricao: string,
  pagina: PaginaEtiqueta,
  gerar: (p: PaginaEtiqueta) => ModeloEtiqueta['definicao']['elementos'],
): ModeloEtiqueta {
  return {
    chave: `preset:${slug}`,
    nome,
    descricao: descricao || undefined,
    fonte: 'volume',
    id: null,
    // `blocos` vazio = "o layout padrão da fonte" (gerarVolume): o envio não
    // tem caixas de marcar; quem quer mudar usa o editor visual.
    definicao: { pagina, elementos: gerar(pagina), layout_auto: { blocos: [] } },
  };
}

// A4 cortada em 4 (ou folha adesiva de 4): 105 × 148,5 mm, sem margem.
const A4_EM_4 = folha(A4, { largura: 105, altura: 148.5, colunas: 2, linhas: 2 }, { topo: 0, esquerda: 0, passoHorizontal: 105 });

export const PRESETS_VOLUME: ModeloEtiqueta[] = [
  presetEnvio('volume-100x150', 'Volume 100 × 150 mm', 'padrão de transportadora', bobina(100, 150), gerarVolume),
  presetEnvio('volume-100x100', 'Volume 100 × 100 mm', '', bobina(100, 100), gerarVolume),
  presetEnvio('volume-100x50', 'Volume 100 × 50 mm', 'compacta', bobina(100, 50), gerarVolume),
  presetEnvio('volume-a4-4', 'Volume — folha A4 em 4', 'impressora comum', A4_EM_4, gerarVolume),
];

/** DANFE Simplificado – Etiqueta: layout fixo (NT 2020.004), só o papel muda. */
export const PRESETS_DANFE: ModeloEtiqueta[] = [
  presetEnvio('danfe-100x150', 'DANFE Simplificado 100 × 150 mm', '', bobina(100, 150), gerarDanfe),
  presetEnvio('danfe-a4-4', 'DANFE Simplificado — folha A4 em 4', 'impressora comum', A4_EM_4, gerarDanfe),
];

/**
 * Etiqueta por volume do MÓVEL da marcenaria (Spec 14 D4). Lista PRÓPRIA: não
 * entra em `PRESETS` nem em `PRESETS_VOLUME`, então a tela de envio e o editor
 * de modelos da loja não mudam. `fonte: 'volume'` (o tipo não muda e o backend
 * dos modelos também não). O primeiro é o padrão: folha comum, sem térmica.
 */
export const PRESETS_MOVEL: ModeloEtiqueta[] = [
  presetEnvio('movel-a4-4', 'Móvel — folha A4 em 4', 'impressora comum', A4_EM_4, gerarMovel),
  presetEnvio('movel-100x150', 'Móvel 100 × 150 mm', 'térmica', bobina(100, 150), gerarMovel),
  presetEnvio('movel-100x50', 'Móvel 100 × 50 mm', 'térmica, compacta', bobina(100, 50), gerarMovel),
];
