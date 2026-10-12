/**
 * Spec 04B (marcenaria, D3) — o "Sofre perda" só viaja no cadastro do produto
 * no segmento com orçamento técnico. Nos outros, o corpo enviado é IDÊNTICO
 * ao de antes (caso 21).
 */
import { describe, expect, it } from 'vitest';

import { campoSofrePerda } from '../sofrePerda';

describe('campoSofrePerda', () => {
  it('21 — informática (sem orçamento técnico): nada é acrescentado ao corpo', () => {
    expect(campoSofrePerda(false, true)).toEqual({});
    expect(campoSofrePerda(false, false)).toEqual({});
    // Espalhado no corpo, não cria a chave.
    expect({ nome: 'X', ...campoSofrePerda(false, true) }).toEqual({ nome: 'X' });
  });

  it('marcenaria: manda o valor da caixa (desmarcada = false)', () => {
    expect(campoSofrePerda(true, true)).toEqual({ sofre_perda: true });
    expect(campoSofrePerda(true, false)).toEqual({ sofre_perda: false });
    expect(campoSofrePerda(true, undefined)).toEqual({ sofre_perda: false });
  });
});
