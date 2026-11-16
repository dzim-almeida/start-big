/**
 * Spec 06B §11 — caso 14: o texto de cada aviso do motor, com e sem custos (§6.6).
 */
import { describe, expect, it } from 'vitest';

import { textoDoAviso, textosDosAvisos } from '../constants/avisos.constants';

describe('avisos do motor', () => {
  it('14 — tabela §6.6 com e sem custos', () => {
    expect(textoDoAviso('INSUMO_SEM_CUSTO', true)?.texto).toBe(textoDoAviso('INSUMO_SEM_CUSTO', false)?.texto);
    expect(textoDoAviso('HORAS_SEM_CUSTO_HORA', true)?.texto).toContain('custo/hora');
    expect(textoDoAviso('HORAS_SEM_CUSTO_HORA', false)).toBeNull();          // vendedor não vê mão de obra
    expect(textoDoAviso('MARGEM_NEGATIVA', true)?.texto).toContain('margem líquida está negativa');
    expect(textoDoAviso('MARGEM_NEGATIVA', false)?.texto).toBe(
      'O desconto deixou o orçamento abaixo do custo. Fale com o responsável antes de enviar.',
    );
    expect(textoDoAviso('ORCAMENTO_VAZIO', false)?.tom).toBe('neutro');
  });

  it('código desconhecido (spec futura) não aparece', () => {
    expect(textoDoAviso('AVISO_DO_FUTURO', true)).toBeNull();
    expect(textosDosAvisos(['AVISO_DO_FUTURO', 'INSUMO_SEM_CUSTO'], true).map((a) => a.codigo)).toEqual(['INSUMO_SEM_CUSTO']);
  });
});
