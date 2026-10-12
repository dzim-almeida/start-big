/**
 * Spec 06B §11 — casos 01 a 03: conversões entre a tela e a API (PR4).
 * A API só trabalha com inteiros; a tela, com números "de gente".
 */
import { describe, expect, it } from 'vitest';

import {
  bpParaPercentual,
  formatarBp,
  formatarMedidas,
  formatarQuantidade,
  horasParaCentesimos,
  lerNumeroDigitado,
  milesimosParaQuantidade,
  numeroParaTexto,
  percentualParaBp,
  quantidadeParaMilesimos,
  reaisParaCentavos,
} from '../utils/conversoes';

describe('conversões (PR4)', () => {
  it('01 — R$ arredonda, nunca trunca: 0,1 + 0,2 vira 30 centavos', () => {
    expect(reaisParaCentavos(0.1 + 0.2)).toBe(30);       // 0,30000000000000004 em ponto flutuante
    expect(reaisParaCentavos(19.999)).toBe(2000);
  });

  it('02 — quantidade de insumo em milésimos: 1,4 chapa = 1400', () => {
    expect(quantidadeParaMilesimos(1.4)).toBe(1400);
    expect(quantidadeParaMilesimos(0.001)).toBe(1);
    expect(milesimosParaQuantidade(26000)).toBe(26);
  });

  it('03 — medidas: vazia vira "—"; nenhuma medida, nada', () => {
    expect(formatarMedidas(700, null, 600)).toBe('700 × — × 600 mm');
    expect(formatarMedidas(700, 2200, 600)).toBe('700 × 2200 × 600 mm');
    expect(formatarMedidas(null, null, null)).toBe('');
  });

  it('percentual ↔ bp e horas ↔ centésimos', () => {
    expect(percentualParaBp(12.35)).toBe(1235);
    expect(bpParaPercentual(9000)).toBe(90);
    expect(horasParaCentesimos(2.5)).toBe(250);
    expect(formatarBp(3660)).toBe('36,6%');
    expect(formatarQuantidade(1400)).toBe('1,4');
  });

  it('lê o número digitado do jeito brasileiro e do americano', () => {
    expect(lerNumeroDigitado('1,4')).toBe(1.4);
    expect(lerNumeroDigitado('1.4')).toBe(1.4);           // um ponto sem vírgula é a vírgula
    expect(lerNumeroDigitado('1.234,56')).toBe(1234.56);
    expect(lerNumeroDigitado('R$ 10')).toBe(10);
    expect(lerNumeroDigitado('')).toBe(0);
    expect(lerNumeroDigitado('abc')).toBeNull();
    expect(lerNumeroDigitado('-3')).toBeNull();
    expect(numeroParaTexto(1.4, 3)).toBe('1,4');
  });
});
