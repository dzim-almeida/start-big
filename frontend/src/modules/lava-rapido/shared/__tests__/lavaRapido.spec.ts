/**
 * Funções puras do lava-rápido (Specs 03B e 04B): placa, WhatsApp, previsão e
 * tempo no pátio.
 */
import { describe, expect, it } from 'vitest';

import {
  linkWhatsApp,
  mensagemPronto,
  normalizarPlaca,
  previsaoDeEntrega,
  telefoneWhatsApp,
  tempoNoPatio,
} from '../utils/lavaRapido';

describe('normalizarPlaca', () => {
  it('maiúscula, sem hífen nem espaço', () => {
    expect(normalizarPlaca('abc-1d23')).toBe('ABC1D23');
    expect(normalizarPlaca(' abc 1234 ')).toBe('ABC1234');
  });
  it('placa estrangeira passa (sem regex no segmento)', () => {
    expect(normalizarPlaca('AB 123 CD')).toBe('AB123CD');
  });
});

describe('WhatsApp (SPEC-00 O8)', () => {
  it('põe o 55 e tira a máscara', () => {
    expect(telefoneWhatsApp('(88) 99999-1234')).toBe('5588999991234');
    expect(telefoneWhatsApp('5588999991234')).toBe('5588999991234');
  });
  it('sem DDD ou vazio: null (o botão some)', () => {
    expect(telefoneWhatsApp('99991234')).toBeNull();
    expect(telefoneWhatsApp(null)).toBeNull();
    expect(linkWhatsApp('', 'oi')).toBeNull();
  });
  it('mensagem com o primeiro nome, o veículo e a placa', () => {
    expect(mensagemPronto('João da Silva', 'Gol', 'ABC1D23'))
      .toBe('Olá, João! Seu Gol, placa ABC1D23 está pronto para retirada. Obrigado!');
    expect(mensagemPronto(null, null, null)).toBe('Olá! Seu veículo está pronto para retirada. Obrigado!');
  });
  it('link wa.me com o texto codificado', () => {
    expect(linkWhatsApp('88999991234', 'Olá João')).toBe('https://wa.me/5588999991234?text=Ol%C3%A1%20Jo%C3%A3o');
  });
});

describe('previsaoDeEntrega (SPEC-00 O4)', () => {
  const agora = new Date('2026-11-12T13:00:00Z');
  it('agora + soma das durações', () => {
    expect(previsaoDeEntrega(agora, [30, 15])?.toISOString()).toBe('2026-11-12T13:45:00.000Z');
  });
  it('sem duração nenhuma: sem previsão (melhor que uma errada)', () => {
    expect(previsaoDeEntrega(agora, [null, 0, undefined])).toBeNull();
  });
});

describe('tempoNoPatio', () => {
  const agora = new Date('2026-11-12T14:10:00Z');
  it('lê o horário do backend como UTC, com ou sem Z', () => {
    expect(tempoNoPatio('2026-11-12T13:45:00', agora)).toBe('há 25 min');
    expect(tempoNoPatio('2026-11-12T13:45:00Z', agora)).toBe('há 25 min');
  });
  it('horas e minutos', () => {
    expect(tempoNoPatio('2026-11-12T13:00:00', agora)).toBe('há 1 h 10 min');
    expect(tempoNoPatio('2026-11-12T12:10:00', agora)).toBe('há 2 h');
  });
});
