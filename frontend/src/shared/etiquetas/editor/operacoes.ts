/**
 * @fileoverview Operações do editor visual (plano §5.5, fase 3), sem tela.
 *
 * Tudo em milímetros e tudo IMUTÁVEL: cada operação devolve um elemento novo.
 * É o que deixa o desfazer (Ctrl+Z) ser só uma pilha de fotografias da lista.
 *
 * Nenhuma operação deixa um elemento sair da etiqueta: o backend recusaria o
 * modelo (422), e o lojista não saberia qual dos elementos arrastou para fora.
 */

import type { CampoEtiqueta } from '../campos';
import { fontePara } from '../layoutAuto';
import { arredondar, type ElementoEtiqueta, type PaginaEtiqueta } from '../modelo';

/** Passo do "ímã" ao arrastar. Com Alt, o arraste fica livre (0,1 mm). */
export const PASSO_MM = 0.5;
export const PASSO_FINO_MM = 0.1;

/** Menor caixa que ainda dá para pegar com o mouse. */
const MINIMO_MM = 2;

export function encaixarNoPasso(valor: number, passo = PASSO_MM): number {
  return arredondar(Math.round(valor / passo) * passo, 2);
}

/** Linha tem altura zero de propósito: só a largura é redimensionável. */
function alturaMinima(el: ElementoEtiqueta): number {
  return el.tipo === 'linha' ? 0 : MINIMO_MM;
}

/** Caixa com largura zero é a linha VERTICAL (ver teste.ts): largura mínima zero. */
function larguraMinima(el: ElementoEtiqueta): number {
  return el.tipo === 'caixa' && el.w === 0 ? 0 : MINIMO_MM;
}

function limitar(valor: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, valor));
}

export function mover(el: ElementoEtiqueta, pagina: PaginaEtiqueta, x: number, y: number, passo = PASSO_MM): ElementoEtiqueta {
  return {
    ...el,
    x: limitar(encaixarNoPasso(x, passo), 0, arredondar(pagina.largura_mm - el.w)),
    y: limitar(encaixarNoPasso(y, passo), 0, arredondar(pagina.altura_mm - el.h)),
  };
}

export function redimensionar(el: ElementoEtiqueta, pagina: PaginaEtiqueta, w: number, h: number, passo = PASSO_MM): ElementoEtiqueta {
  const minW = larguraMinima(el);
  const minH = alturaMinima(el);
  return {
    ...el,
    w: minW === 0 && el.w === 0 ? 0 : limitar(encaixarNoPasso(w, passo), minW, arredondar(pagina.largura_mm - el.x)),
    h: el.tipo === 'linha' ? 0 : limitar(encaixarNoPasso(h, passo), minH, arredondar(pagina.altura_mm - el.y)),
  };
}

/**
 * Traz para dentro o que sobrou fora depois de a etiqueta DIMINUIR (o
 * lojista trocou 60 × 40 por 40 × 25 com o layout manual já montado).
 * Primeiro encolhe o que não cabe nem sozinho, depois empurra para dentro.
 */
export function encaixar(el: ElementoEtiqueta, pagina: PaginaEtiqueta): ElementoEtiqueta {
  const w = Math.min(el.w, pagina.largura_mm);
  const h = Math.min(el.h, pagina.altura_mm);
  return {
    ...el,
    w,
    h,
    x: arredondar(limitar(el.x, 0, pagina.largura_mm - w)),
    y: arredondar(limitar(el.y, 0, pagina.altura_mm - h)),
  };
}

export function saiDaEtiqueta(el: ElementoEtiqueta, pagina: PaginaEtiqueta): boolean {
  return el.x + el.w > pagina.largura_mm + 0.5 || el.y + el.h > pagina.altura_mm + 0.5;
}

export type TipoNovoElemento = 'campo' | 'texto' | 'barras' | 'qr' | 'linha' | 'caixa';

export const NOVOS_ELEMENTOS: { tipo: TipoNovoElemento; rotulo: string }[] = [
  { tipo: 'campo', rotulo: 'Dado do produto' },
  { tipo: 'texto', rotulo: 'Texto fixo' },
  { tipo: 'barras', rotulo: 'Código de barras' },
  { tipo: 'qr', rotulo: 'QR Code' },
  { tipo: 'linha', rotulo: 'Linha' },
  { tipo: 'caixa', rotulo: 'Moldura' },
];

/** Campos com que um elemento novo nasce — os da fonte do modelo. */
export interface CamposPadrao {
  texto: CampoEtiqueta;
  codigo: CampoEtiqueta;
  qr: CampoEtiqueta;
}

export const PADRAO_PRODUTO: CamposPadrao = {
  texto: 'produto.nome',
  codigo: 'produto.codigo_barras',
  qr: 'produto.codigo_produto',
};

export const PADRAO_VOLUME: CamposPadrao = {
  texto: 'destinatario.nome',
  codigo: 'envio.codigo',
  qr: 'envio.codigo',
};

/** Um elemento novo, no canto superior esquerdo, num tamanho que cabe. */
export function novoElemento(tipo: TipoNovoElemento, pagina: PaginaEtiqueta, padrao: CamposPadrao = PADRAO_PRODUTO): ElementoEtiqueta {
  const W = pagina.largura_mm;
  const H = pagina.altura_mm;
  const x = Math.min(1, W / 10);
  const y = Math.min(1, H / 10);
  const largura = (fracao: number, max: number) => arredondar(Math.min(W - x, Math.max(MINIMO_MM, Math.min(max, W * fracao))), 1);
  const altura = (fracao: number, max: number) => arredondar(Math.min(H - y, Math.max(MINIMO_MM, Math.min(max, H * fracao))), 1);

  switch (tipo) {
    case 'campo':
    case 'texto': {
      const h = altura(0.25, 6);
      return {
        tipo: 'texto', x, y, w: largura(0.8, 60), h,
        ...(tipo === 'campo' ? { campo: padrao.texto } : { texto: 'Texto' }),
        fonte_pt: fontePara(h, 1), negrito: false, alinhamento: 'esquerda', linhas_max: 1,
      };
    }
    case 'barras':
      return { tipo: 'barras', x, y, w: largura(0.8, 50), h: altura(0.4, 15), campo: padrao.codigo, simbologia: 'auto', legenda: true };
    case 'qr': {
      const lado = Math.min(largura(0.4, 20), altura(0.6, 20));
      return { tipo: 'qr', x, y, w: lado, h: lado, campo: padrao.qr };
    }
    case 'linha':
      return { tipo: 'linha', x, y: arredondar(H / 2, 1), w: largura(0.8, 80), h: 0, espessura_mm: 0.3 };
    case 'caixa':
      return { tipo: 'caixa', x: 0, y: 0, w: W, h: H, espessura_mm: 0.3 };
  }
}

/** Os problemas da lista de elementos, com o número que o lojista vê no editor. */
export function problemasDosElementos(elementos: ElementoEtiqueta[], pagina: PaginaEtiqueta): string[] {
  if (elementos.length === 0) return ['Adicione pelo menos um elemento à etiqueta.'];
  return elementos.flatMap((el, i) =>
    saiDaEtiqueta(el, pagina) ? [`O elemento ${i + 1} sai da etiqueta — use "Trazer tudo para dentro".`] : [],
  );
}
