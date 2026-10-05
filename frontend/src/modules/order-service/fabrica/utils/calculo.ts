/**
 * @fileoverview Espelho de backend-fastapi/app/services/fabrica/calculo.py, só
 * para a PRÉVIA na tela enquanto o orçamento é digitado. Quem vale é o
 * servidor: salvar recalcula tudo lá. Mesmas regras — inteiros, perda só em
 * quem "sofre perda", custo da FRAÇÃO de chapa (sem arredondar a chapa).
 *
 * Os testes (`__tests__/calculo.spec.ts`) usam os mesmos exemplos do backend:
 * se um lado mudar e o outro não, um deles quebra.
 */

import type { UnidadeConsumo } from '../types/fabrica.types';

const BASE_BP = 10_000;

/** ⌈ consumo × (1 + perda) ⌉ — só em insumo que sofre perda. */
export function consumoComPerda(consumo: number, perdaBp: number, sofrePerda: boolean): number {
  if (!sofrePerda || perdaBp === 0) return consumo;
  return Math.ceil((consumo * (BASE_BP + perdaBp)) / BASE_BP);
}

/** Custo, em centavos, da fração de unidade de compra que o móvel usa. */
export function custoDoMaterial(
  consumo: number,
  perdaBp: number,
  sofrePerda: boolean,
  consumoPorUnidade: number,
  custoUnitario: number,
): number {
  if (consumoPorUnidade <= 0) return 0;
  const usado = consumoComPerda(consumo, perdaBp, sofrePerda);
  // meio para cima, como o backend: ⌊(2a + b) / 2b⌋
  return Math.floor((2 * usado * custoUnitario + consumoPorUnidade) / (2 * consumoPorUnidade));
}

// --- O que o usuário digita ↔ o inteiro do servidor --------------------------

const FATOR: Record<UnidadeConsumo, number> = { M2: 1_000_000, M: 1_000, UN: 1 };

/** "4,4" m² → 4.400.000 mm²; "12" m → 12.000 mm; "6" un → 6. */
export function consumoParaInteiro(unidade: UnidadeConsumo, valor: number | null): number | null {
  if (valor == null || !Number.isFinite(valor) || valor <= 0) return null;
  const inteiro = Math.round(valor * FATOR[unidade]);
  return inteiro >= 1 ? inteiro : null;
}

export function consumoParaTela(unidade: UnidadeConsumo, inteiro: number): number {
  return inteiro / FATOR[unidade];
}

export const ROTULO_CONSUMO: Record<UnidadeConsumo, string> = { M2: 'm²', M: 'm', UN: 'un' };

/** Pontos-base ↔ percentual da tela (1000 ↔ 10). */
export function bpParaPercentual(bp: number): number {
  return bp / 100;
}

export function percentualParaBp(percentual: number | null): number {
  if (percentual == null || !Number.isFinite(percentual)) return 0;
  return Math.round(percentual * 100);
}
