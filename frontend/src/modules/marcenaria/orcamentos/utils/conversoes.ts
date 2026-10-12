/**
 * @fileoverview Conversões entre o que a tela mostra e o que a API guarda
 * (Spec 06B §7.7). A API trabalha só com inteiros (PR4): centavos, basis
 * points (1235 = 12,35%), milésimos de insumo (1,4 chapa = 1400) e milímetros.
 *
 * NENHUM cálculo de preço acontece aqui (C8): só troca de unidade.
 */

/** R$ (número da tela) → centavos. Arredonda, nunca trunca: 0,1 + 0,2 vira 30. */
export const reaisParaCentavos = (reais: number): number => Math.round(reais * 100);

/** Centavos → R$ (para preencher um campo de dinheiro). */
export const centavosParaReais = (centavos: number): number => centavos / 100;

/** % (número da tela) → basis points: 12,35% → 1235. */
export const percentualParaBp = (percentual: number): number => Math.round(percentual * 100);

/** Basis points → % (para preencher um campo de percentual): 1235 → 12,35. */
export const bpParaPercentual = (bp: number): number => bp / 100;

/** Quantidade de insumo (até 3 casas) → milésimos: 1,4 → 1400. */
export const quantidadeParaMilesimos = (quantidade: number): number => Math.round(quantidade * 1000);

/** Milésimos → número da tela: 1400 → 1,4. */
export const milesimosParaQuantidade = (milesimos: number): number => milesimos / 1000;

/** Horas (2,5) → centésimos (250), como a mão de obra por horas é guardada. */
export const horasParaCentesimos = (horas: number): number => Math.round(horas * 100);

/** Centésimos de hora → horas da tela: 250 → 2,5. */
export const centesimosParaHoras = (centesimos: number): number => centesimos / 100;

/**
 * Medidas para a lista: (700, 2200, 600) → "700 × 2200 × 600 mm".
 * Medida vazia sai como "—"; móvel sem nenhuma medida não mostra nada.
 */
export function formatarMedidas(l?: number | null, a?: number | null, p?: number | null): string {
  if (l == null && a == null && p == null) return '';
  return `${[l, a, p].map((m) => (m == null ? '—' : m)).join(' × ')} mm`;
}

/** Margem e percentuais em bp → texto: 3660 → "36,6%". */
export const formatarBp = (bp: number): string =>
  `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;

/** Quantidade de insumo em milésimos → texto com até 3 casas: 1400 → "1,4". */
export const formatarQuantidade = (milesimos: number): string =>
  milesimosParaQuantidade(milesimos).toLocaleString('pt-BR', { maximumFractionDigits: 3 });

/**
 * Número digitado na tela → número: "1,4" → 1.4; "1.234,56" → 1234.56;
 * "R$ 10" → 10; vazio → 0. Texto que não é número (ou negativo) → null,
 * e a tela espera o usuário corrigir.
 *
 * Ponto: com vírgula no texto, o ponto é separador de milhar ("1.234,56");
 * sem vírgula, UM ponto é a vírgula de quem digitou no jeito americano
 * ("1.4" = 1,4 chapa, nunca 14). Vários pontos sem vírgula = milhar.
 */
export function lerNumeroDigitado(texto: string): number | null {
  let limpo = texto.replace(/R\$|\s/g, '');
  const pontos = (limpo.match(/\./g) ?? []).length;
  if (limpo.includes(',') || pontos > 1) limpo = limpo.replace(/\./g, '');   // ponto = milhar
  limpo = limpo.replace(',', '.');
  if (limpo === '') return 0;
  const numero = Number(limpo);
  return Number.isFinite(numero) && numero >= 0 ? numero : null;
}

/** Número → texto com vírgula e até `casas` decimais, sem separador de milhar: 1.4 → "1,4". */
export const numeroParaTexto = (numero: number, casas: number): string =>
  numero.toLocaleString('pt-BR', { maximumFractionDigits: casas, useGrouping: false });
