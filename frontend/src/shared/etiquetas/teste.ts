/**
 * @fileoverview Página de teste para calibrar a impressora (plano §5.4).
 *
 * Calibração é o maior assunto de suporte do mercado (Tiny/Olist dedica uma
 * página inteira a "meça o rolo com a régua"). O teste imprime o CONTORNO de
 * cada posição e uma cruz no centro: se a borda sai cortada ou a cruz fora do
 * meio, o lojista vê de quanto deslocar — sem gastar etiqueta com produto.
 */

import { arredondar, etiquetasPorPagina, type DefinicaoEtiqueta } from './modelo';
import type { ValoresEtiqueta } from './campos';

export function definicaoDeTeste(original: DefinicaoEtiqueta, nome: string): DefinicaoEtiqueta {
  const { largura_mm: w, altura_mm: h } = original.pagina;
  const meioX = arredondar(w / 2, 1);
  const meioY = arredondar(h / 2, 1);
  const fonte = Math.max(4, Math.min(10, h / 6));

  return {
    pagina: original.pagina,
    elementos: [
      { tipo: 'caixa', x: 0, y: 0, w, h, espessura_mm: 0.3 },
      { tipo: 'linha', x: meioX - 3, y: meioY, w: 6, h: 0, espessura_mm: 0.3 },
      { tipo: 'caixa', x: meioX, y: meioY - 3, w: 0, h: 6, espessura_mm: 0.15 },
      {
        tipo: 'texto', x: 1, y: 1, w: w - 2, h: Math.min(h / 3, 6),
        texto: nome, fonte_pt: fonte, negrito: true, alinhamento: 'centro', linhas_max: 1,
      },
      {
        tipo: 'texto', x: 1, y: h - 1 - Math.min(h / 3, 6), w: w - 2, h: Math.min(h / 3, 6),
        texto: `${w.toLocaleString('pt-BR')} × ${h.toLocaleString('pt-BR')} mm`,
        fonte_pt: fonte, alinhamento: 'centro', linhas_max: 1,
      },
    ],
  };
}

/** Uma página cheia: a fileira inteira do rolo, ou a folha inteira. */
export function etiquetasDeTeste(definicao: DefinicaoEtiqueta): ValoresEtiqueta[] {
  return Array.from({ length: etiquetasPorPagina(definicao.pagina) }, () => ({}));
}
