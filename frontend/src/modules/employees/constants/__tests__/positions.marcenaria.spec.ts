/**
 * Spec 04B (marcenaria) — linha "Custos da Marcenaria" na tela de Cargos
 * (casos 07, 08, 22 e 23).
 *
 * A linha usa o mecanismo `segmento` que a matriz já tem: fica fora do nível
 * de acesso e só aparece na marcenaria. O retrato de PERMISSION_KEYS e dos
 * níveis (positions.fabrica.spec.ts, gravado antes) continua valendo.
 */
import { describe, expect, it } from 'vitest';

import {
  ALL_PERMISSION_KEYS,
  PERMISSION_KEYS,
  PERMISSION_MATRIX,
  chavesAoAlternar,
} from '@/modules/employees/constants/positions.constants';

describe('linha "Custos da Marcenaria"', () => {
  it('07 — não entra na conta do nível do cargo', () => {
    expect(PERMISSION_KEYS).not.toContain('view_custos_marcenaria');
    expect(PERMISSION_KEYS).not.toContain('manage_custos_marcenaria');
  });

  it('08 — existe só para a marcenaria, com as chaves que o backend confere', () => {
    const linha = PERMISSION_MATRIX.find((item) => item.id === 'marcenaria_custos');
    expect(linha?.segmento).toBe('marcenaria');
    expect(linha?.deleteKey).toBeUndefined();                     // sem Excluir
    expect(ALL_PERMISSION_KEYS).toEqual(
      expect.arrayContaining(['view_custos_marcenaria', 'manage_custos_marcenaria']),
    );
  });
});

describe('Gerenciar e Ver andam juntos só nas linhas de segmento', () => {
  it('23 — marcar Gerenciar marca Ver junto', () => {
    expect(chavesAoAlternar('manage_custos_marcenaria', true)).toEqual(['manage_custos_marcenaria', 'view_custos_marcenaria']);
  });

  it('desmarcar Ver desmarca Gerenciar junto', () => {
    expect(chavesAoAlternar('view_custos_marcenaria', false)).toEqual(['view_custos_marcenaria', 'manage_custos_marcenaria']);
  });

  it('marcar só Ver, ou desmarcar só Gerenciar, mexe só nela', () => {
    expect(chavesAoAlternar('view_custos_marcenaria', true)).toEqual(['view_custos_marcenaria']);
    expect(chavesAoAlternar('manage_custos_marcenaria', false)).toEqual(['manage_custos_marcenaria']);
  });

  it('22 — nas linhas de sempre nada muda: só a própria chave', () => {
    for (const chave of ['manage_products', 'view_products', 'manage_purchases', 'view_financeiro']) {
      expect(chavesAoAlternar(chave, true)).toEqual([chave]);
      expect(chavesAoAlternar(chave, false)).toEqual([chave]);
    }
  });
});

/**
 * Spec 06B (marcenaria, D51; caso 27) — linha "Orçamentos de Marcenaria".
 * Mesmo mecanismo `segmento` da linha de custos: fora do nível de acesso e
 * invisível nos outros segmentos (o PositionModal filtra por `item.segmento`).
 */
describe('linha "Orçamentos de Marcenaria"', () => {
  const linha = () => PERMISSION_MATRIX.find((item) => item.id === 'marcenaria_orcamentos');

  it('existe só para a marcenaria, com Ver, Gerenciar e Excluir', () => {
    expect(linha()).toMatchObject({
      segmento: 'marcenaria',
      viewKey: 'view_orcamentos_marcenaria',
      manageKey: 'manage_orcamentos_marcenaria',
      deleteKey: 'delete_orcamentos_marcenaria',
    });
  });

  it('fica ANTES de "Custos da Marcenaria"', () => {
    const ids = PERMISSION_MATRIX.map((item) => item.id);
    expect(ids.indexOf('marcenaria_orcamentos')).toBe(ids.indexOf('marcenaria_custos') - 1);
  });

  it('27 — informática: a linha não aparece e o "Selecionar tudo" não muda', () => {
    // A mesma regra do PositionModal: linha de segmento só no segmento dela.
    const visivel = PERMISSION_MATRIX.filter((item) => !item.segmento || item.segmento === 'assistencia_tecnica');
    expect(visivel.find((item) => item.id === 'marcenaria_orcamentos')).toBeUndefined();
    for (const chave of ['view_orcamentos_marcenaria', 'manage_orcamentos_marcenaria', 'delete_orcamentos_marcenaria']) {
      expect(PERMISSION_KEYS).not.toContain(chave);       // nível de acesso igual (retrato do positions.fabrica)
    }
  });

  it('marcar Gerenciar ou Excluir marca Ver; desmarcar Ver tira os dois', () => {
    expect(chavesAoAlternar('manage_orcamentos_marcenaria', true)).toEqual(['manage_orcamentos_marcenaria', 'view_orcamentos_marcenaria']);
    expect(chavesAoAlternar('delete_orcamentos_marcenaria', true)).toEqual(['delete_orcamentos_marcenaria', 'view_orcamentos_marcenaria']);
    expect(chavesAoAlternar('view_orcamentos_marcenaria', false)).toEqual([
      'view_orcamentos_marcenaria', 'manage_orcamentos_marcenaria', 'delete_orcamentos_marcenaria',
    ]);
    expect(chavesAoAlternar('delete_orcamentos_marcenaria', false)).toEqual(['delete_orcamentos_marcenaria']);
  });
});
