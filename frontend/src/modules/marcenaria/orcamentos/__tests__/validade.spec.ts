/**
 * Spec 06B §7.12 e D49: "vence em 2 dias", "vence hoje", "venceu há 3 dias",
 * pela data LOCAL (a validade é data pura, sem fuso).
 */
import { describe, expect, it } from 'vitest';

import { diasAteValidade, textoValidade, tomValidade } from '../utils/validade';

const HOJE = new Date(2026, 9, 9, 23, 30);                 // 09/10/2026, 23:30 (perto da meia-noite de propósito)

describe('validade', () => {
  it('conta dias inteiros pela data local', () => {
    expect(diasAteValidade('2026-10-09', HOJE)).toBe(0);
    expect(diasAteValidade('2026-10-11', HOJE)).toBe(2);
    expect(diasAteValidade('2026-10-06', HOJE)).toBe(-3);
  });

  it('textos e tons', () => {
    expect(textoValidade('2026-10-11', HOJE)).toBe('vence em 2 dias');
    expect(textoValidade('2026-10-10', HOJE)).toBe('vence amanhã');
    expect(textoValidade('2026-10-09', HOJE)).toBe('vence hoje');
    expect(textoValidade('2026-10-08', HOJE)).toBe('venceu ontem');
    expect(textoValidade('2026-10-06', HOJE)).toBe('venceu há 3 dias');
    expect(tomValidade('2026-10-11', HOJE)).toBe('atencao');
    expect(tomValidade('2026-10-30', HOJE)).toBe('normal');
    expect(tomValidade('2026-10-06', HOJE)).toBe('vencido');
  });
});
