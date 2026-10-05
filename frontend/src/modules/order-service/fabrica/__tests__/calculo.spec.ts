import { describe, expect, it } from 'vitest';

import {
  consumoComPerda,
  consumoParaInteiro,
  consumoParaTela,
  custoDoMaterial,
  percentualParaBp,
} from '../utils/calculo';

// Os MESMOS exemplos de backend-fastapi/test/services/fabrica/test_calculo.py.
const CHAPA = 2750 * 1850;
const M2 = 1_000_000;

describe('prévia do orçamento — espelho do backend', () => {
  it('12 m² com 10% de perda viram 13,2 m²', () => {
    expect(consumoComPerda(12 * M2, 1000, true)).toBe(13_200_000);
  });

  it('insumo sem perda não ganha perda', () => {
    expect(consumoComPerda(24, 1000, false)).toBe(24);
  });

  it('perda arredonda o consumo para cima', () => {
    expect(consumoComPerda(1, 1000, true)).toBe(2);
  });

  it('custo do móvel usa a fração de chapa', () => {
    expect(custoDoMaterial(M2, 1000, true, CHAPA, 30000)).toBe(6486);
    expect(custoDoMaterial(4 * M2, 1000, true, CHAPA, 30000)).toBe(25946);
    expect(custoDoMaterial(12_000, 1000, true, 50_000, 2000)).toBe(528);
  });
});

describe('conversões da tela', () => {
  it('m², metro e unidade viram o inteiro do servidor', () => {
    expect(consumoParaInteiro('M2', 4.4)).toBe(4_400_000);
    expect(consumoParaInteiro('M', 12)).toBe(12_000);
    expect(consumoParaInteiro('UN', 6)).toBe(6);
    expect(consumoParaInteiro('M2', 0)).toBeNull();
    expect(consumoParaInteiro('UN', null)).toBeNull();
  });

  it('e voltam para a tela', () => {
    expect(consumoParaTela('M2', 4_400_000)).toBe(4.4);
    expect(consumoParaTela('M', 12_000)).toBe(12);
  });

  it('percentual ↔ pontos-base', () => {
    expect(percentualParaBp(10)).toBe(1000);
    expect(percentualParaBp(12.5)).toBe(1250);
    expect(percentualParaBp(null)).toBe(0);
  });
});
