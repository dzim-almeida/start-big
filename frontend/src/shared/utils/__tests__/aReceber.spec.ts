import { describe, expect, it } from 'vitest';

import { rotuloAReceber } from '../aReceber';

const HOJE = new Date(2026, 9, 12); // 12/10/2026

describe('rotuloAReceber', () => {
  it('pagamento na hora (sem vencimento): sem selo', () => {
    expect(rotuloAReceber(undefined, HOJE)).toBeNull();
    expect(rotuloAReceber(null, HOJE)).toBeNull();
    expect(rotuloAReceber('', HOJE)).toBeNull();
  });

  it('mesmo ano: dia/mês', () => {
    expect(rotuloAReceber('2026-10-30', HOJE)).toBe('A receber em 30/10');
  });

  it('outro ano: com o ano, para janeiro não parecer este', () => {
    expect(rotuloAReceber('2027-01-15', HOJE)).toBe('A receber em 15/01/2027');
  });

  it('não escorrega um dia pelo fuso (lê a data como texto)', () => {
    expect(rotuloAReceber('2026-11-01', HOJE)).toBe('A receber em 01/11');
  });
});
