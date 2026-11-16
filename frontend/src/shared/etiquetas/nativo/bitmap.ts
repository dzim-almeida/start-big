/**
 * @fileoverview Bitmap monocromático de uma página de etiqueta.
 *
 * Linhas de cima para baixo; cada byte leva 8 pontos, o mais à esquerda no
 * bit mais alto. Aqui 1 = ponto PRETO — cada linguagem converte para a sua
 * polaridade (ver linguagens.ts).
 */

export interface Bitmap {
  largura: number;
  altura: number;
  bytesPorLinha: number;
  dados: Uint8Array;
}

export function bitmapVazio(largura: number, altura: number): Bitmap {
  const bytesPorLinha = Math.ceil(largura / 8);
  return { largura, altura, bytesPorLinha, dados: new Uint8Array(bytesPorLinha * altura) };
}

export function pintar(bitmap: Bitmap, x: number, y: number): void {
  if (x < 0 || y < 0 || x >= bitmap.largura || y >= bitmap.altura) return;
  bitmap.dados[y * bitmap.bytesPorLinha + (x >> 3)] |= 0x80 >> (x & 7);
}

/**
 * Converte RGBA (de um canvas) em bitmap. Limiar de 50% na luminância: o
 * texto vem com borda suavizada, e a térmica só tem preto ou branco.
 */
export function deRgba(rgba: Uint8ClampedArray, largura: number, altura: number): Bitmap {
  const bitmap = bitmapVazio(largura, altura);
  for (let y = 0; y < altura; y++) {
    for (let x = 0; x < largura; x++) {
      const i = (y * largura + x) * 4;
      const alfa = rgba[i + 3] / 255;
      // Fundo transparente conta como branco.
      const luminancia = (0.299 * rgba[i] + 0.587 * rgba[i + 1] + 0.114 * rgba[i + 2]) * alfa + 255 * (1 - alfa);
      if (luminancia < 128) pintar(bitmap, x, y);
    }
  }
  return bitmap;
}
