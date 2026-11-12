/**
 * Spec 08B — funções de data da agenda.
 */
import { describe, expect, it } from 'vitest';

import { diaISO, diasDaSemana, instanteDoBackend } from '../composables/useAgenda';

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
