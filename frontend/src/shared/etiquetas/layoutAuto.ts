/**
 * @fileoverview Layout automático: gera os elementos de uma etiqueta a partir
 * do tamanho dela e de QUAIS dados o lojista quer impresso.
 *
 * É o que deixa a configuração "fácil" antes do editor visual (plano §9, fase
 * 3): quem tem um rolo 45 × 28 não precisa posicionar nada — informa as
 * medidas, marca "nome, preço e código de barras" e o layout se ajusta. O
 * editor, quando vier, parte destes mesmos elementos.
 *
 * Etiqueta larga e baixa (gôndola, 100 × 30) ganha duas colunas: textos à
 * esquerda, barras à direita. Empilhar tudo numa etiqueta de 30 mm deixaria
 * o código de barras baixo demais para o leitor.
 */

import type { CampoEtiqueta } from './campos';
import { arredondar, type ElementoEtiqueta, type PaginaEtiqueta, type Alinhamento } from './modelo';

export type BlocoAuto =
  | 'empresa'
  | 'nome'
  | 'marca'
  | 'localizacao'
  | 'preco_varejo'
  | 'preco_atacado'
  | 'barras'
  | 'codigo_produto';

export interface OpcoesLayoutAuto {
  blocos: BlocoAuto[];
}

export const BLOCOS_AUTO: { bloco: BlocoAuto; rotulo: string }[] = [
  { bloco: 'empresa', rotulo: 'Nome da empresa' },
  { bloco: 'nome', rotulo: 'Nome do produto' },
  { bloco: 'marca', rotulo: 'Marca' },
  { bloco: 'localizacao', rotulo: 'Localização no estoque' },
  { bloco: 'preco_varejo', rotulo: 'Preço de varejo' },
  { bloco: 'preco_atacado', rotulo: 'Preço de atacado' },
  { bloco: 'barras', rotulo: 'Código de barras' },
  { bloco: 'codigo_produto', rotulo: 'Código interno (texto)' },
];

// Ordem de cima para baixo e peso na altura disponível.
const ORDEM: BlocoAuto[] = BLOCOS_AUTO.map((b) => b.bloco);
const PESO: Record<BlocoAuto, number> = {
  empresa: 0.8,
  nome: 2,
  marca: 0.8,
  localizacao: 0.8,
  preco_varejo: 1.8,
  preco_atacado: 0.8,
  barras: 3.2,
  codigo_produto: 0.8,
};

const TEXTO_DO_BLOCO: Partial<Record<BlocoAuto, { campo: CampoEtiqueta; prefixo?: string; negrito?: boolean }>> = {
  empresa: { campo: 'empresa.nome' },
  nome: { campo: 'produto.nome', negrito: true },
  marca: { campo: 'produto.marca' },
  localizacao: { campo: 'produto.localizacao_estoque', prefixo: 'Loc. ' },
  preco_varejo: { campo: 'preco.varejo', negrito: true },
  preco_atacado: { campo: 'preco.atacado', prefixo: 'Atacado ' },
  codigo_produto: { campo: 'produto.codigo_produto', prefixo: 'Cód. ' },
};

const PT_EM_MM = 0.3528;

/** Maior corpo de letra (pt) que cabe `linhas` linhas em `alturaMm`. */
function fontePara(alturaMm: number, linhas: number): number {
  const pt = alturaMm / linhas / PT_EM_MM / 1.2;
  return Math.max(4, Math.min(40, Math.floor(pt * 2) / 2));
}

interface Caixa {
  x: number;
  y: number;
  w: number;
  h: number;
}

function empilhar(blocos: BlocoAuto[], area: Caixa, alinhamento: Alinhamento): ElementoEtiqueta[] {
  if (blocos.length === 0) return [];
  const folga = Math.min(1, area.h * 0.03);
  const pesoTotal = blocos.reduce((soma, b) => soma + PESO[b], 0);
  const util = area.h - folga * (blocos.length - 1);

  let y = area.y;
  return blocos.map((bloco) => {
    const h = (util * PESO[bloco]) / pesoTotal;
    const caixa = { x: area.x, y, w: area.w, h };
    y += h + folga;
    return elementoDoBloco(bloco, caixa, alinhamento);
  });
}

function elementoDoBloco(bloco: BlocoAuto, c: Caixa, alinhamento: Alinhamento): ElementoEtiqueta {
  const caixa = { x: arredondar(c.x, 1), y: arredondar(c.y, 1), w: arredondar(c.w, 1), h: arredondar(c.h, 1) };

  if (bloco === 'barras') {
    return {
      tipo: 'barras',
      ...caixa,
      campo: 'produto.codigo_barras',
      simbologia: 'auto',
      // Abaixo de 8 mm a legenda roubaria altura que falta às barras.
      legenda: caixa.h >= 8,
    };
  }

  const texto = TEXTO_DO_BLOCO[bloco]!;
  // O nome é o único que quebra em duas linhas, e só se couber letra legível.
  const linhas = bloco === 'nome' && caixa.h >= 6 ? 2 : 1;
  return {
    tipo: 'texto',
    ...caixa,
    campo: texto.campo,
    texto: texto.prefixo,
    fonte_pt: fontePara(caixa.h, linhas),
    negrito: texto.negrito ?? false,
    alinhamento,
    linhas_max: linhas,
  };
}

export function gerarElementos(pagina: PaginaEtiqueta, opcoes: OpcoesLayoutAuto): ElementoEtiqueta[] {
  const { largura_mm: w, altura_mm: h } = pagina;
  const margem = Math.max(1, Math.min(3, Math.min(w, h) * 0.06));
  const area: Caixa = { x: margem, y: margem, w: w - 2 * margem, h: h - 2 * margem };

  const blocos = ORDEM.filter((b) => opcoes.blocos.includes(b));
  const temBarras = blocos.includes('barras');
  const larga = temBarras && blocos.length > 1 && w / h >= 2.6;

  if (!larga) return empilhar(blocos, area, 'centro');

  const textos = blocos.filter((b) => b !== 'barras');
  const larguraTexto = area.w * 0.52;
  const inicioBarras = area.x + area.w * 0.55;
  return [
    ...empilhar(textos, { ...area, w: larguraTexto }, 'esquerda'),
    elementoDoBloco('barras', { x: inicioBarras, y: area.y, w: area.x + area.w - inicioBarras, h: area.h }, 'centro'),
  ];
}
