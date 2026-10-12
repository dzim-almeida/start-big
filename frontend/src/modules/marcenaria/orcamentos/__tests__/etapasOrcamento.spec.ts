/**
 * Etapas do orçamento no cabeçalho do editor (redesign 10/2026).
 */
import { describe, expect, it } from 'vitest';

import { etapasDoOrcamento } from '../utils/etapasOrcamento';

const estados = (...args: Parameters<typeof etapasDoOrcamento>) => etapasDoOrcamento(...args).map((e) => e.estado);

describe('etapas do orçamento', () => {
  it('rascunho (e o "novo", ainda sem status): a primeira é a atual', () => {
    expect(estados('RASCUNHO', false)).toEqual(['atual', 'pendente', 'pendente', 'pendente']);
    expect(estados(undefined, false)).toEqual(['atual', 'pendente', 'pendente', 'pendente']);
  });

  it('enviado, vencido e recusado param em "Enviado"', () => {
    for (const status of ['ENVIADO', 'VENCIDO', 'RECUSADO'] as const) {
      expect(estados(status, false)).toEqual(['concluida', 'atual', 'pendente', 'pendente']);
    }
  });

  it('aprovado: "Aprovado" atual; com a OS gerada, a OS é a atual', () => {
    expect(estados('APROVADO', false)).toEqual(['concluida', 'concluida', 'atual', 'pendente']);
    expect(estados('APROVADO', true)).toEqual(['concluida', 'concluida', 'concluida', 'atual']);
  });

  it('substituído: nenhuma etapa (a versão nova é que anda)', () => {
    expect(estados('SUBSTITUIDO', false)).toEqual(['pendente', 'pendente', 'pendente', 'pendente']);
  });

  it('os rótulos, na ordem', () => {
    expect(etapasDoOrcamento('RASCUNHO', false).map((e) => e.rotulo)).toEqual(['Rascunho', 'Enviado', 'Aprovado', 'OS']);
  });
});
