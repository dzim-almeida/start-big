import { describe, expect, it } from 'vitest';
import {
  formatarNumeroQuantidade,
  formatarQuantidade,
  formatarQuantidadeSemUnidade,
  normalizarQuantidade,
  unidadeEhFracionada,
} from '../quantidade';

describe('quantidade fracionada (venda fracionada)', () => {
  it('unidades a granel, com ² ³ e sem diferenciar maiúscula', () => {
    for (const u of ['kg', 'G', 'l', 'ML', 'm', 'cm', 'M2', 'm²', 'M³']) expect(unidadeEhFracionada(u)).toBe(true);
    for (const u of ['UN', 'CX', 'PC', null, '']) expect(unidadeEhFracionada(u)).toBe(false);
  });

  it('3 casas, sem o resto do ponto flutuante', () => {
    expect(normalizarQuantidade(1.1 + 1)).toBe(2.1);
    expect(normalizarQuantidade(0.1234)).toBe(0.123);
    expect(normalizarQuantidade(3)).toBe(3);
  });

  it('número com vírgula no fracionado, inteiro no resto', () => {
    expect(formatarNumeroQuantidade(3.5, 'KG')).toBe('3,5');
    expect(formatarNumeroQuantidade(3, 'KG')).toBe('3');
    expect(formatarNumeroQuantidade(0.125, 'kg')).toBe('0,125');
    expect(formatarNumeroQuantidade(3, 'UN')).toBe('3');
    // O campo relê o que mostra: sem separador de milhar.
    expect(formatarNumeroQuantidade(1234.5, 'KG')).toBe('1234,5');
    expect(formatarNumeroQuantidade(1000, 'UN')).toBe('1000');
    expect(formatarQuantidade(3.5, 'KG')).toBe('3,5 kg');
  });

  it('sem unidade (item da nota): vírgula no quebrado, inteiro igual ao de sempre', () => {
    expect(formatarQuantidadeSemUnidade(3.5)).toBe('3,5');
    expect(formatarQuantidadeSemUnidade(3)).toBe('3');
    expect(formatarQuantidadeSemUnidade(1000)).toBe('1000');
    expect(formatarQuantidadeSemUnidade(null)).toBe('0');
  });
});
