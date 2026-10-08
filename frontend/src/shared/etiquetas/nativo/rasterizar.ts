/**
 * @fileoverview Desenha uma página de etiquetas na resolução da térmica.
 *
 * Mesmo desenho do `EtiquetaView` (preview/driver), em outro pincel: aqui é
 * um canvas em PONTOS da impressora (203 ou 300 dpi), depois reduzido a preto
 * e branco. Duas diferenças de propósito em relação ao preview:
 *
 * - O código de barras NÃO estica para a caixa. Cada barra tem um número
 *   inteiro de pontos; esticada, a térmica arredonda umas barras para cima e
 *   outras para baixo, e o leitor do caixa passa a errar. A barra sai do
 *   tamanho inteiro que cabe na caixa, centralizada.
 * - O texto é quebrado aqui (o canvas não tem "line-clamp"), com a mesma
 *   regra: palavras inteiras, reticências na última linha que couber.
 */

import JsBarcode from 'jsbarcode';
import QRCode from 'qrcode';

import { resolverCodigo } from '../codigoBarras';
import { valorDoCodigo, type ValoresEtiqueta } from '../campos';
import { posicaoNaPagina, type DefinicaoEtiqueta, type ElementoEtiqueta, type ElementoTexto } from '../modelo';
import type { Posicionada } from '../paginacao';
import { deRgba, type Bitmap } from './bitmap';

const FONTE = 'Arial, Helvetica, sans-serif';

interface Escala {
  /** Pontos por milímetro. */
  k: number;
  dpi: number;
}

function criarCanvas(largura: number, altura: number): CanvasRenderingContext2D {
  const canvas = document.createElement('canvas');
  canvas.width = largura;
  canvas.height = altura;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Este computador não conseguiu desenhar a etiqueta (canvas indisponível).');
  return ctx;
}

// --- Texto -----------------------------------------------------------------

function textoDoElemento(el: ElementoTexto, valores: ValoresEtiqueta): string {
  const valor = el.campo ? (valores[el.campo] ?? '') : '';
  if (el.campo && !valor) return '';
  return `${el.texto ?? ''}${valor}`;
}

/** Quebra em até `maximo` linhas que cabem em `largura`; reticências se sobrar. */
export function quebrarTexto(
  texto: string,
  largura: number,
  maximo: number,
  medir: (s: string) => number,
): string[] {
  const palavras = texto.split(/\s+/).filter(Boolean);
  const linhas: string[] = [];
  let atual = '';
  let truncado = false;

  for (const palavra of palavras) {
    const tentativa = atual ? `${atual} ${palavra}` : palavra;
    if (medir(tentativa) <= largura) {
      atual = tentativa;
      continue;
    }
    if (atual) {
      linhas.push(atual);
      atual = '';
      if (linhas.length === maximo) {
        truncado = true;
        break;
      }
    }
    // Palavra que sozinha não cabe: corta por caractere.
    let resto = palavra;
    while (medir(resto) > largura && resto.length > 1) {
      let corte = resto.length - 1;
      while (corte > 1 && medir(resto.slice(0, corte)) > largura) corte--;
      linhas.push(resto.slice(0, corte));
      resto = resto.slice(corte);
      if (linhas.length === maximo) {
        truncado = true;
        break;
      }
    }
    if (truncado) break;
    atual = resto;
  }
  if (!truncado && atual) {
    if (linhas.length < maximo) linhas.push(atual);
    else truncado = true;
  }

  if (truncado && linhas.length) {
    let ultima = linhas[linhas.length - 1];
    while (ultima.length > 0 && medir(`${ultima}…`) > largura) ultima = ultima.slice(0, -1);
    linhas[linhas.length - 1] = `${ultima.trimEnd()}…`;
  }
  return linhas;
}

function desenharTexto(ctx: CanvasRenderingContext2D, el: ElementoTexto, valores: ValoresEtiqueta, e: Escala, x: number, y: number) {
  const conteudo = textoDoElemento(el, valores);
  if (!conteudo) return;
  const w = el.w * e.k;
  const h = el.h * e.k;
  const px = (el.fonte_pt * e.dpi) / 72;
  const alturaLinha = px * 1.2;

  ctx.font = `${el.negrito ? 'bold ' : ''}${px}px ${FONTE}`;
  ctx.textBaseline = 'top';
  const linhas = quebrarTexto(conteudo, w, el.linhas_max ?? 1, (s) => ctx.measureText(s).width);

  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  // Centralizado na vertical, como o flex do EtiquetaView.
  let topo = y + (h - linhas.length * alturaLinha) / 2 + (alturaLinha - px) / 2;
  for (const linha of linhas) {
    const largura = ctx.measureText(linha).width;
    const esquerda =
      el.alinhamento === 'centro' ? x + (w - largura) / 2 : el.alinhamento === 'direita' ? x + w - largura : x;
    ctx.fillText(linha, esquerda, topo);
    topo += alturaLinha;
  }
  ctx.restore();
}

// --- Código de barras ------------------------------------------------------

function desenharBarras(
  ctx: CanvasRenderingContext2D,
  el: Extract<ElementoEtiqueta, { tipo: 'barras' }>,
  valores: ValoresEtiqueta,
  e: Escala,
  x: number,
  y: number,
) {
  const codigo = resolverCodigo(valorDoCodigo(valores, el.campo), el.simbologia);
  if (!codigo) return;
  const w = el.w * e.k;
  const h = el.h * e.k;
  const alturaLegendaMm = el.legenda ? Math.min(3.2, el.h * 0.22) : 0;
  const alturaLegenda = alturaLegendaMm * e.k;
  const alturaBarras = Math.max(1, Math.floor(h - alturaLegenda));

  // 1ª passada com 1 ponto por módulo só para saber quantos módulos o código tem.
  const medida = document.createElement('canvas');
  JsBarcode(medida, codigo.valor, { format: codigo.simbologia, width: 1, height: 1, margin: 0, displayValue: false });
  const modulos = medida.width;
  const pontosPorModulo = Math.max(1, Math.floor(w / modulos));

  const barras = document.createElement('canvas');
  JsBarcode(barras, codigo.valor, {
    format: codigo.simbologia,
    width: pontosPorModulo,
    height: alturaBarras,
    margin: 0,
    displayValue: false,
    // Sem isto o EAN/UPC desenha as barras-guia mais compridas, e elas descem
    // por cima da legenda — no papel, os números saem riscados.
    flat: true,
    background: '#ffffff',
    lineColor: '#000000',
  });
  const esquerda = Math.round(x + Math.max(0, (w - barras.width) / 2));

  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(barras, esquerda, Math.round(y));

  if (el.legenda && alturaLegenda > 0) {
    const pt = alturaLegendaMm / 0.3528 / 1.15;
    const px = (pt * e.dpi) / 72;
    ctx.font = `${px}px ${FONTE}`;
    ctx.textBaseline = 'top';
    const largura = ctx.measureText(codigo.valor).width;
    ctx.fillText(codigo.valor, x + (w - largura) / 2, y + alturaBarras + (alturaLegenda - px) / 2);
  }
  ctx.restore();
}

// --- QR, linha, moldura ----------------------------------------------------

function desenharQr(ctx: CanvasRenderingContext2D, valor: string, x: number, y: number, w: number, h: number) {
  if (!valor) return;
  const { modules } = QRCode.create(valor, { errorCorrectionLevel: 'M' });
  const celula = Math.max(1, Math.floor(Math.min(w, h) / modules.size));
  const lado = celula * modules.size;
  const x0 = Math.round(x + (w - lado) / 2);
  const y0 = Math.round(y + (h - lado) / 2);
  for (let linha = 0; linha < modules.size; linha++) {
    for (let coluna = 0; coluna < modules.size; coluna++) {
      if (modules.get(linha, coluna)) ctx.fillRect(x0 + coluna * celula, y0 + linha * celula, celula, celula);
    }
  }
}

function desenharElemento(ctx: CanvasRenderingContext2D, el: ElementoEtiqueta, valores: ValoresEtiqueta, e: Escala, ox: number, oy: number) {
  const x = ox + el.x * e.k;
  const y = oy + el.y * e.k;
  const w = el.w * e.k;
  const h = el.h * e.k;
  ctx.fillStyle = '#000000';

  switch (el.tipo) {
    case 'texto':
      return desenharTexto(ctx, el, valores, e, x, y);
    case 'barras':
      return desenharBarras(ctx, el, valores, e, x, y);
    case 'qr':
      return desenharQr(ctx, valores[el.campo] ?? '', x, y, w, h);
    case 'linha':
      return ctx.fillRect(x, y, Math.max(1, w), Math.max(1, el.espessura_mm * e.k));
    case 'caixa': {
      const t = Math.max(1, el.espessura_mm * e.k);
      ctx.fillRect(x, y, Math.max(t, w), t);
      ctx.fillRect(x, y + h - t, Math.max(t, w), t);
      ctx.fillRect(x, y, t, h);
      ctx.fillRect(x + w - t, y, t, h);
      return;
    }
  }
}

/**
 * Uma página (uma fileira do rolo) em bitmap, com a calibração do terminal
 * aplicada. `larguraMm × alturaMm` é o papel inteiro da página.
 */
export function rasterizarPagina(
  definicao: DefinicaoEtiqueta,
  pagina: Posicionada<ValoresEtiqueta>[],
  opcoes: { dpi: 203 | 300; larguraMm: number; alturaMm: number; deslocamentoX: number; deslocamentoY: number },
): Bitmap {
  const e: Escala = { k: opcoes.dpi / 25.4, dpi: opcoes.dpi };
  const largura = Math.round(opcoes.larguraMm * e.k);
  const altura = Math.round(opcoes.alturaMm * e.k);
  const ctx = criarCanvas(largura, altura);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, largura, altura);

  for (const { posicao, item } of pagina) {
    const { x, y } = posicaoNaPagina(definicao.pagina, posicao);
    const ox = (x + opcoes.deslocamentoX) * e.k;
    const oy = (y + opcoes.deslocamentoY) * e.k;
    for (const el of definicao.elementos) desenharElemento(ctx, el, item, e, ox, oy);
  }
  return deRgba(ctx.getImageData(0, 0, largura, altura).data, largura, altura);
}
