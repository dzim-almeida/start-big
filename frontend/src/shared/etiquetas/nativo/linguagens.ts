/**
 * @fileoverview Etiqueta → bytes da linguagem da térmica (plano §5.4, fase 4).
 *
 * "Modo imagem": cada página chega aqui já desenhada como bitmap na resolução
 * da impressora (ver rasterizar.ts) e vai como GRÁFICO. Um caminho só para as
 * três linguagens, acento que sai certo (as fontes internas das térmicas são
 * o ponto fraco com "ç" e "ã") e o papel igual ao preview.
 *
 * Polaridade do bit — cada linguagem tem a sua, e errar sai tudo preto:
 * - ZPL (^GFA): 1 = ponto impresso.
 * - TSPL (BITMAP): 0 = ponto impresso (manual TSC / exemplos de BITMAP).
 * - EPL (GW): o manual não diz; segue a convenção do TSPL (0 = impresso). A
 *   opção "inverter cores" do terminal existe para o caso de ser o contrário.
 *
 * Páginas iguais em sequência viram UM comando com quantidade (^PQ / PRINT /
 * P): 40 etiquetas do mesmo produto são uma imagem só no cabo.
 */

import type { Bitmap } from './bitmap';

export type LinguagemEtiqueta = 'zpl' | 'tspl' | 'epl';

export interface ConfigNativa {
  dpi: 203 | 300;
  /** Tamanho do papel (uma página): o rolo inteiro × uma etiqueta. */
  larguraMm: number;
  alturaMm: number;
  gapMm: number;
  /** 0–15; nulo = a da impressora. */
  escuridao: number | null;
  girar180: boolean;
  inverter: boolean;
}

export interface PaginaRasterizada {
  bitmap: Bitmap;
  quantidade: number;
}

const texto = new TextEncoder();

function juntar(partes: (string | Uint8Array)[]): Uint8Array {
  const blocos = partes.map((p) => (typeof p === 'string' ? texto.encode(p) : p));
  const total = blocos.reduce((soma, b) => soma + b.length, 0);
  const saida = new Uint8Array(total);
  let posicao = 0;
  for (const bloco of blocos) {
    saida.set(bloco, posicao);
    posicao += bloco.length;
  }
  return saida;
}

function pontos(mm: number, dpi: number): number {
  return Math.round((mm * dpi) / 25.4);
}

/** Os dados com 1 = impresso, já considerando o "inverter" do terminal. */
function dadosComPretoIgual(bitmap: Bitmap, pretoEhUm: boolean, inverter: boolean): Uint8Array {
  // O bitmap chega com 1 = preto. Inverte se a linguagem pede 0 = preto, e
  // inverte de novo se o terminal pediu.
  const precisaInverter = pretoEhUm === inverter;
  if (!precisaInverter) return bitmap.dados;
  return bitmap.dados.map((b) => ~b & 0xff);
}

// ---------------------------------------------------------------------------
// ZPL
// ---------------------------------------------------------------------------

/** Letras de repetição da compressão ASCII do ZPL: G=1…Y=19, g=20…z=400. */
function contagemZpl(n: number): string {
  let s = '';
  while (n >= 400) {
    s += 'z';
    n -= 400;
  }
  if (n >= 20) {
    s += String.fromCharCode('g'.charCodeAt(0) + Math.floor(n / 20) - 1);
    n %= 20;
  }
  if (n > 0) s += String.fromCharCode('G'.charCodeAt(0) + n - 1);
  return s;
}

/**
 * Uma linha em hexa, comprimida: repetições viram contagem + dígito, o fim
 * da linha em branco vira "," e em preto vira "!". Linha igual à anterior
 * vira ":" (no chamador).
 */
export function comprimirLinhaZpl(hexa: string): string {
  let corpo = hexa;
  let final = '';
  const zeros = corpo.match(/0+$/);
  const uns = corpo.match(/F+$/);
  if (zeros && zeros[0].length > 1) {
    corpo = corpo.slice(0, -zeros[0].length);
    final = ',';
  } else if (uns && uns[0].length > 1) {
    corpo = corpo.slice(0, -uns[0].length);
    final = '!';
  }

  let saida = '';
  for (let i = 0; i < corpo.length; ) {
    let j = i;
    while (j < corpo.length && corpo[j] === corpo[i]) j++;
    const repeticoes = j - i;
    saida += (repeticoes > 1 ? contagemZpl(repeticoes) : '') + corpo[i];
    i = j;
  }
  return saida + final;
}

export function graficoZpl(bitmap: Bitmap, inverter: boolean): string {
  const dados = dadosComPretoIgual(bitmap, true, inverter);
  const { bytesPorLinha, altura } = bitmap;
  let anterior = '';
  let saida = '';
  for (let y = 0; y < altura; y++) {
    let hexa = '';
    for (let x = 0; x < bytesPorLinha; x++) {
      hexa += dados[y * bytesPorLinha + x].toString(16).padStart(2, '0').toUpperCase();
    }
    saida += hexa === anterior ? ':' : comprimirLinhaZpl(hexa);
    anterior = hexa;
  }
  const total = bytesPorLinha * altura;
  return `^GFA,${total},${total},${bytesPorLinha},${saida}`;
}

export function gerarZpl(paginas: PaginaRasterizada[], cfg: ConfigNativa): Uint8Array {
  const largura = pontos(cfg.larguraMm, cfg.dpi);
  const altura = pontos(cfg.alturaMm, cfg.dpi);
  const partes: string[] = [];
  // ~SD vai de 0 a 30; a escala do terminal é 0–15.
  if (cfg.escuridao != null) partes.push(`~SD${String(Math.round(cfg.escuridao * 2)).padStart(2, '0')}\n`);
  for (const { bitmap, quantidade } of paginas) {
    partes.push(
      '^XA\n',
      `^PW${largura}\n^LL${altura}\n^LH0,0\n^PO${cfg.girar180 ? 'I' : 'N'}\n`,
      `^FO0,0${graficoZpl(bitmap, cfg.inverter)}^FS\n`,
      `^PQ${quantidade}\n`,
      '^XZ\n',
    );
  }
  return juntar(partes);
}

// ---------------------------------------------------------------------------
// TSPL
// ---------------------------------------------------------------------------

function mm(valor: number): string {
  return String(Math.round(valor * 10) / 10);
}

export function gerarTspl(paginas: PaginaRasterizada[], cfg: ConfigNativa): Uint8Array {
  const partes: (string | Uint8Array)[] = [
    `SIZE ${mm(cfg.larguraMm)} mm,${mm(cfg.alturaMm)} mm\r\n`,
    `GAP ${mm(cfg.gapMm)} mm,0 mm\r\n`,
    `DIRECTION ${cfg.girar180 ? 0 : 1}\r\n`,
    'REFERENCE 0,0\r\n',
  ];
  if (cfg.escuridao != null) partes.push(`DENSITY ${Math.round(cfg.escuridao)}\r\n`);
  for (const { bitmap, quantidade } of paginas) {
    partes.push(
      'CLS\r\n',
      `BITMAP 0,0,${bitmap.bytesPorLinha},${bitmap.altura},0,`,
      dadosComPretoIgual(bitmap, false, cfg.inverter),
      '\r\n',
      `PRINT 1,${quantidade}\r\n`,
    );
  }
  return juntar(partes);
}

// ---------------------------------------------------------------------------
// EPL (e PPLB da Argox, que é compatível)
// ---------------------------------------------------------------------------

export function gerarEpl(paginas: PaginaRasterizada[], cfg: ConfigNativa): Uint8Array {
  const largura = pontos(cfg.larguraMm, cfg.dpi);
  const altura = pontos(cfg.alturaMm, cfg.dpi);
  const gap = pontos(cfg.gapMm, cfg.dpi);
  const partes: (string | Uint8Array)[] = ['\n'];
  for (const { bitmap, quantidade } of paginas) {
    partes.push('N\n', `q${largura}\n`, `Q${altura},${gap}\n`, `${cfg.girar180 ? 'ZB' : 'ZT'}\n`);
    if (cfg.escuridao != null) partes.push(`D${Math.round(cfg.escuridao)}\n`);
    partes.push(
      `GW0,0,${bitmap.bytesPorLinha},${bitmap.altura},`,
      dadosComPretoIgual(bitmap, false, cfg.inverter),
      '\n',
      `P${quantidade}\n`,
    );
  }
  return juntar(partes);
}

export function gerarNaLinguagem(linguagem: LinguagemEtiqueta, paginas: PaginaRasterizada[], cfg: ConfigNativa): Uint8Array {
  switch (linguagem) {
    case 'zpl': return gerarZpl(paginas, cfg);
    case 'tspl': return gerarTspl(paginas, cfg);
    case 'epl': return gerarEpl(paginas, cfg);
  }
}
