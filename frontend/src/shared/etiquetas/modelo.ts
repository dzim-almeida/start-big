/**
 * @fileoverview O modelo neutro de etiqueta (docs/etiquetas-plano.md §5.1).
 *
 * Descreve a etiqueta em MILÍMETROS e não pertence a nenhuma linguagem de
 * impressora: o mesmo modelo vira HTML (driver do Windows) hoje, e ZPL, TSPL
 * ou PPLA depois. O espelho deste contrato no backend é
 * `app/schemas/modelo_etiqueta.py` — mexeu num, mexa no outro.
 */

import type { CampoEtiqueta } from './campos';
import type { SimbologiaPreferida } from './codigoBarras';
import type { OpcoesLayoutAuto } from './layoutAuto';

/** De onde vêm os dados: produto (estoque) ou volume de envio (OS/venda). */
export type FonteEtiqueta = 'produto' | 'volume';

export interface FolhaEtiqueta {
  largura_mm: number;
  altura_mm: number;
  linhas: number;
}

/** Uma etiqueta (largura × altura) e como ela se repete no papel. */
export interface PaginaEtiqueta {
  /** `bobina`: rolo de térmica, uma fileira por vez. `folha`: A4/Carta com N linhas. */
  tipo: 'bobina' | 'folha';
  largura_mm: number;
  altura_mm: number;
  colunas: number;
  espaco_colunas_mm: number;
  /** Só vale para folha: na bobina quem avança o papel é o sensor de gap. */
  espaco_linhas_mm: number;
  margem_esq_mm: number;
  margem_topo_mm: number;
  folha: FolhaEtiqueta | null;
}

export type Alinhamento = 'esquerda' | 'centro' | 'direita';

interface ElementoBase {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ElementoTexto extends ElementoBase {
  tipo: 'texto';
  /** Campo de dado impresso. Sem campo, sai o `texto` fixo. */
  campo?: CampoEtiqueta;
  /** Texto fixo, ou prefixo do campo ("Cód: "). */
  texto?: string;
  fonte_pt: number;
  negrito?: boolean;
  alinhamento?: Alinhamento;
  /** Acima disto o texto é cortado com reticências. */
  linhas_max?: number;
}

export interface ElementoBarras extends ElementoBase {
  tipo: 'barras';
  campo: CampoEtiqueta;
  simbologia: SimbologiaPreferida;
  /** Número legível embaixo das barras. */
  legenda: boolean;
}

export interface ElementoQr extends ElementoBase {
  tipo: 'qr';
  campo: CampoEtiqueta;
}

export interface ElementoLinha extends ElementoBase {
  tipo: 'linha';
  espessura_mm: number;
}

export interface ElementoCaixa extends ElementoBase {
  tipo: 'caixa';
  espessura_mm: number;
}

export type ElementoEtiqueta = ElementoTexto | ElementoBarras | ElementoQr | ElementoLinha | ElementoCaixa;

export interface DefinicaoEtiqueta {
  pagina: PaginaEtiqueta;
  elementos: ElementoEtiqueta[];
  /**
   * Opções que GERARAM os elementos pelo layout automático. Presente: o
   * formulário reabre com elas. Ausente: posicionado à mão (editor visual).
   */
  layout_auto?: OpcoesLayoutAuto | null;
}

/** Um modelo pronto para a fila: preset de fábrica ou criado pela loja. */
export interface ModeloEtiqueta {
  /** `preset:<slug>` ou `loja:<id>` — os dois convivem no mesmo seletor. */
  chave: string;
  nome: string;
  descricao?: string;
  fonte: FonteEtiqueta;
  definicao: DefinicaoEtiqueta;
  /** Id no banco; nulo nos presets. */
  id: number | null;
}

/** Quantas etiquetas cabem numa folha (ou numa fileira da bobina). */
export function etiquetasPorPagina(pagina: PaginaEtiqueta): number {
  return pagina.tipo === 'folha' && pagina.folha ? pagina.colunas * pagina.folha.linhas : pagina.colunas;
}

/**
 * Tamanho do papel que o driver recebe (`@page size`).
 *
 * Bobina: a largura do ROLO (todas as colunas + a margem dos DOIS lados — o
 * liner do rolo é simétrico) × a altura de UMA
 * etiqueta — cada página é uma fileira, e o sensor de gap da impressora cuida
 * do espaço entre elas. Folha: a folha inteira.
 */
export function tamanhoDoPapel(pagina: PaginaEtiqueta): { largura_mm: number; altura_mm: number } {
  if (pagina.tipo === 'folha' && pagina.folha) {
    return { largura_mm: pagina.folha.largura_mm, altura_mm: pagina.folha.altura_mm };
  }
  const largura =
    pagina.margem_esq_mm * 2 + pagina.colunas * pagina.largura_mm + (pagina.colunas - 1) * pagina.espaco_colunas_mm;
  return { largura_mm: arredondar(largura), altura_mm: pagina.altura_mm };
}

/** Posição (mm) da etiqueta `indice` dentro da página. */
export function posicaoNaPagina(pagina: PaginaEtiqueta, indice: number): { x: number; y: number } {
  const coluna = indice % pagina.colunas;
  const linha = Math.floor(indice / pagina.colunas);
  return {
    x: pagina.margem_esq_mm + coluna * (pagina.largura_mm + pagina.espaco_colunas_mm),
    y: pagina.tipo === 'folha' ? pagina.margem_topo_mm + linha * (pagina.altura_mm + pagina.espaco_linhas_mm) : 0,
  };
}

/**
 * O que a folha/rolo NÃO comporta — mesmas regras do schema do backend, para
 * o formulário recusar antes de mandar. Vazio = cabe.
 */
export function problemasDaPagina(pagina: PaginaEtiqueta): string[] {
  const problemas: string[] = [];
  if (pagina.largura_mm < 5 || pagina.altura_mm < 5) problemas.push('A etiqueta precisa ter pelo menos 5 × 5 mm.');
  if (pagina.largura_mm > 300 || pagina.altura_mm > 300) problemas.push('A etiqueta pode ter no máximo 300 × 300 mm.');
  if (pagina.tipo !== 'folha' || !pagina.folha) return problemas;

  const { folha } = pagina;
  const largura = pagina.margem_esq_mm + pagina.colunas * pagina.largura_mm + (pagina.colunas - 1) * pagina.espaco_colunas_mm;
  const altura = pagina.margem_topo_mm + folha.linhas * pagina.altura_mm + (folha.linhas - 1) * pagina.espaco_linhas_mm;
  if (largura > folha.largura_mm + 0.5) {
    problemas.push(`As ${pagina.colunas} colunas ocupam ${fmtMm(largura)} e a folha tem ${fmtMm(folha.largura_mm)} de largura.`);
  }
  if (altura > folha.altura_mm + 0.5) {
    problemas.push(`As ${folha.linhas} linhas ocupam ${fmtMm(altura)} e a folha tem ${fmtMm(folha.altura_mm)} de altura.`);
  }
  return problemas;
}

export function fmtMm(valor: number): string {
  return `${arredondar(valor).toLocaleString('pt-BR')} mm`;
}

export function arredondar(valor: number, casas = 2): number {
  const fator = 10 ** casas;
  return Math.round(valor * fator) / fator;
}
