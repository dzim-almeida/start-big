/**
 * Remodelação item 7: validade e prazo pelo calendário (dias ↔ data).
 */
import { describe, expect, it } from 'vitest';

import { dataBase, dataDepoisDe, diasAte } from '../utils/diasPorData';

const hoje = new Date(2026, 9, 13, 21, 30);                 // 13/10/2026 às 21:30 (a hora não pode atrapalhar)

describe('diasPorData', () => {
  it('sem o evento, a base é hoje; com ele, o dia do evento (sem a hora)', () => {
    expect(dataDepoisDe(dataBase(null, hoje), 0)).toBe('2026-10-13');
    expect(dataDepoisDe(dataBase('2026-10-06T23:59:00', hoje), 0)).toBe('2026-10-06');
  });

  it('base + dias = a data (atravessando o mês)', () => {
    expect(dataDepoisDe(dataBase('2026-10-06T13:00:00'), 15)).toBe('2026-10-21');
    expect(dataDepoisDe(dataBase(null, hoje), 30)).toBe('2026-11-12');
  });

  it('a data escolhida vira os dias desde a base', () => {
    expect(diasAte(dataBase('2026-10-06T13:00:00'), '2026-10-21')).toBe(15);
    expect(diasAte(dataBase(null, hoje), '2026-11-12')).toBe(30);
    expect(diasAte(dataBase(null, hoje), '2026-10-13')).toBe(0);   // a própria base
    expect(diasAte(dataBase(null, hoje), '2026-10-10')).toBe(-3);  // data que já passou
  });

  it('ida e volta: dias → data → dias dá o mesmo número', () => {
    const base = dataBase(null, hoje);
    for (const dias of [1, 15, 31, 90, 365]) expect(diasAte(base, dataDepoisDe(base, dias))).toBe(dias);
  });
});
