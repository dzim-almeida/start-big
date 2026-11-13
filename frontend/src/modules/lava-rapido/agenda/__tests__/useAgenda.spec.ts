/**
 * Spec 08B — funções de data da agenda.
 */
import { describe, expect, it } from 'vitest';

import { diaISO, diasDaSemana, diasDoMes, instanteDoBackend } from '../composables/useAgenda';

describe('diasDaSemana', () => {
  it('de segunda a domingo, a partir de qualquer dia', () => {
    const quinta = new Date(2026, 10, 12);                 // 12/11/2026 é quinta
    const semana = diasDaSemana(quinta).map(diaISO);
    expect(semana[0]).toBe('2026-11-09');                  // segunda
    expect(semana[6]).toBe('2026-11-15');                  // domingo
  });
  it('domingo pertence à semana que começou na segunda anterior', () => {
    expect(diaISO(diasDaSemana(new Date(2026, 10, 15))[0])).toBe('2026-11-09');
  });
});

describe('instanteDoBackend', () => {
  it('sem "Z" é UTC', () => {
    expect(instanteDoBackend('2026-11-12T12:00:00').toISOString()).toBe('2026-11-12T12:00:00.000Z');
    expect(instanteDoBackend('2026-11-12T12:00:00Z').toISOString()).toBe('2026-11-12T12:00:00.000Z');
  });
});

describe('diasDoMes', () => {
  it('6 semanas de segunda a domingo cobrindo o mês inteiro', () => {
    const grade = diasDoMes(new Date(2026, 10, 20)).map(diaISO);   // novembro/2026
    expect(grade).toHaveLength(42);
    expect(grade[0]).toBe('2026-10-26');                   // segunda antes do dia 1º (domingo)
    expect(grade).toContain('2026-11-01');
    expect(grade).toContain('2026-11-30');
    expect(grade[41]).toBe('2026-12-06');
  });
});
