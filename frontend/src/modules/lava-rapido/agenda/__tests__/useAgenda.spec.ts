/**
 * Spec 08B — funções de data da agenda.
 */
import { describe, expect, it } from 'vitest';

import { diaISO, diasDaSemana, diasDoMes, instanteDoBackend, ocupacaoNoHorario } from '../composables/useAgenda';
import type { Agendamento } from '../../shared/schemas/agenda.schema';

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

describe('ocupacaoNoHorario (aviso de vagas, SPEC-00 O11)', () => {
  const base = {
    cliente_id: null, cliente_nome: 'X', cliente_contato: null, placa: null, veiculo: null,
    tipo_veiculo: null, porte_id: null, servicos: [], observacao: null, numero_os: null, criado_em: '',
  };
  // Instantes do backend: UTC sem "Z".
  const ag = (id: number, inicioUtc: string, duracao: number | null, situacao: Agendamento['situacao'] = 'AGENDADO') =>
    ({ ...base, id, inicio: inicioUtc, duracao_minutos: duracao, situacao }) as Agendamento;
  const as = (isoUtc: string) => new Date(`${isoUtc}Z`);

  it('conta quem se sobrepõe ao intervalo escolhido', () => {
    const lista = [ag(1, '2026-11-14T12:00:00', 60), ag(2, '2026-11-14T12:30:00', 30), ag(3, '2026-11-14T14:00:00', 30)];
    expect(ocupacaoNoHorario(lista, as('2026-11-14T12:45:00'), 30)).toBe(2);
    expect(ocupacaoNoHorario(lista, as('2026-11-14T13:00:00'), 30)).toBe(0); // 12:00+60 termina às 13:00
  });

  it('sem duração vale 30 min; cancelado e não veio não ocupam; o próprio não conta', () => {
    const lista = [
      ag(1, '2026-11-14T12:00:00', null),
      ag(2, '2026-11-14T12:00:00', 60, 'CANCELADO'),
      ag(3, '2026-11-14T12:00:00', 60, 'NAO_VEIO'),
      ag(4, '2026-11-14T12:00:00', 60, 'CHEGOU'),
    ];
    expect(ocupacaoNoHorario(lista, as('2026-11-14T12:15:00'), null)).toBe(2);
    expect(ocupacaoNoHorario(lista, as('2026-11-14T12:15:00'), null, 4)).toBe(1);
    expect(ocupacaoNoHorario(lista, as('2026-11-14T12:30:00'), null, 4)).toBe(0);
  });
});
