import { describe, expect, it } from 'vitest';

import { areaDaChapa, comprimentoEmMm, descreverRendimento } from '../utils/insumo';

describe('insumo da fábrica — conversões da tela', () => {
  it('chapa 2750×1850 vira mm² inteiro', () => {
    expect(areaDaChapa(2750, 1850)).toBe(5_087_500);
  });

  it('medida faltando ou inválida não gera área', () => {
    expect(areaDaChapa(2750, null)).toBeNull();
    expect(areaDaChapa(0, 1850)).toBeNull();
    expect(areaDaChapa(-1, 1850)).toBeNull();
  });

  it('rolo em metros vira mm', () => {
    expect(comprimentoEmMm(50)).toBe(50_000);
    expect(comprimentoEmMm(2.75)).toBe(2_750);
    expect(comprimentoEmMm(null)).toBeNull();
  });

  it('descreve o rendimento para ler', () => {
    expect(descreverRendimento('M2', 5_087_500)).toBe('5,0875 m²');
    expect(descreverRendimento('M', 50_000)).toBe('50 m');
    expect(descreverRendimento('UN', 100)).toBe('100 un');
    expect(descreverRendimento('M2', null)).toBe('—');
  });
});
