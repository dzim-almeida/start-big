import { describe, expect, it } from 'vitest';

import { calcularRecebidoOS } from '../recebidoOS';

// Tudo em centavos, como o backend.

describe('calcularRecebidoOS — OS normal', () => {
  it('adiantamento + linhas, e imprime as linhas', () => {
    const r = calcularRecebidoOS({
      valor_total: 10000, valor_entrada: 3000, pagamentos: [{ valor: 7000 }],
    });
    expect(r.totalRecebido).toBe(10000);
    expect(r.listarLinhas).toBe(true);
    expect(r.creditoAnterior).toBe(0);
  });

  it('adiantamento maior que o total só abate até o total', () => {
    const r = calcularRecebidoOS({ valor_total: 5000, valor_entrada: 8000, pagamentos: [] });
    expect(r.adiantamento).toBe(8000);
    expect(r.adiantamentoUtilizado).toBe(5000);
    expect(r.totalRecebido).toBe(5000);
  });
});

describe('calcularRecebidoOS — OS reaberta', () => {
  it('uma reabertura: crédito + o pago depois, sem somar as linhas antigas duas vezes', () => {
    // OS de 100, adiantou 30, pagou 70. Reabriu: crédito 100, adiantamentos 30.
    // Subiu para 150, pagou 50.
    const r = calcularRecebidoOS({
      valor_total: 15000, valor_entrada: 0,
      credito_anterior: 10000, adiantamentos_anteriores: 3000,
      pagamentos: [{ valor: 7000 }, { valor: 5000 }],
    });
    expect(r.listarLinhas).toBe(false);
    expect(r.pagamentosAposReabertura).toBe(5000);
    expect(r.totalRecebido).toBe(15000);
  });

  it('o pagamento novo menor que o adiantamento antigo NÃO é engolido (regressão de 19/09/2026)', () => {
    // OS de 100, adiantou 60, pagou 40. Reabriu: crédito 100, adiantamentos 60.
    // Subiu para 150, pagou 50. A conta antiga fazia max(0, 90 − 100) = 0 e o
    // recibo dizia "recebido 100" para um cliente que tinha pago 150.
    const r = calcularRecebidoOS({
      valor_total: 15000, valor_entrada: 0,
      credito_anterior: 10000, adiantamentos_anteriores: 6000,
      pagamentos: [{ valor: 4000 }, { valor: 5000 }],
    });
    expect(r.pagamentosAposReabertura).toBe(5000);
    expect(r.totalRecebido).toBe(15000);
  });

  it('duas reaberturas: o crédito acumulado já traz tudo, e nada foi pago depois', () => {
    // Depois da 2ª reabertura: crédito 150 (70+50 linhas + 30 adiantamento).
    const r = calcularRecebidoOS({
      valor_total: 15000, valor_entrada: 0,
      credito_anterior: 15000, adiantamentos_anteriores: 3000,
      pagamentos: [{ valor: 7000 }, { valor: 5000 }],
    });
    expect(r.pagamentosAposReabertura).toBe(0);
    expect(r.totalRecebido).toBe(15000);
  });

  it('OS reaberta antes da correção (sem adiantamentos_anteriores) segue somando certo quando não havia adiantamento', () => {
    const r = calcularRecebidoOS({
      valor_total: 14000, valor_entrada: 0,
      credito_anterior: 14000,
      pagamentos: [{ valor: 14000 }],
    });
    expect(r.pagamentosAposReabertura).toBe(0);
    expect(r.totalRecebido).toBe(14000);
  });

  it('novo adiantamento depois de reabrir entra na conta', () => {
    const r = calcularRecebidoOS({
      valor_total: 20000, valor_entrada: 2000,
      credito_anterior: 10000, adiantamentos_anteriores: 3000,
      pagamentos: [{ valor: 7000 }],
    });
    expect(r.totalRecebido).toBe(12000);
  });
});
