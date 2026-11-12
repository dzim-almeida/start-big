/**
 * Spec 02B do lava-rápido — grade "porte → preço e duração" no cadastro de serviço.
 * Só as funções puras: o que vai para o PUT a partir do que está na tela.
 */
import { describe, expect, it } from 'vitest';

import { minutosDoTexto, montarPrecos } from '../composables/usePrecosPorPorteForm';

describe('minutosDoTexto', () => {
  it('inteiro positivo; vazio, zero e lixo viram null', () => {
    expect(minutosDoTexto('40')).toBe(40);
    expect(minutosDoTexto(' 45 ')).toBe(45);
    expect(minutosDoTexto('30,5')).toBe(30);
    for (const t of ['', '0', '-5', 'abc']) expect(minutosDoTexto(t)).toBeNull();
  });

  it('teto de 24 h', () => {
    expect(minutosDoTexto('5000')).toBe(24 * 60);
  });
});

describe('montarPrecos', () => {
  it('reais viram centavos; porte sem preço fica de fora (volta ao padrão)', () => {
    const precos = montarPrecos({
      1: { valor: 40, duracao: '30' },
      2: { valor: 59.9, duracao: '' },
      3: { valor: undefined, duracao: '50' },                       // sem preço: duração não grava
      4: { valor: null as unknown as undefined, duracao: '' },      // MoneyInput limpo manda null
    });
    expect(precos).toEqual([
      { porte_id: 1, valor: 4000, duracao_minutos: 30 },
      { porte_id: 2, valor: 5990, duracao_minutos: null },
    ]);
  });

  it('preço zero é preço (lavagem de cortesia), não ausência', () => {
    expect(montarPrecos({ 7: { valor: 0, duracao: '' } })).toEqual([
      { porte_id: 7, valor: 0, duracao_minutos: null },
    ]);
  });
});
