import { describe, expect, it } from 'vitest';

import {
  ALL_PERMISSION_KEYS,
  PERMISSION_KEYS,
  PERMISSION_MATRIX,
  applyEndpointPermissions,
} from '@/modules/employees/constants/positions.constants';

describe('linha "Fábrica" de Cargos', () => {
  it('existe só para a marcenaria', () => {
    const linha = PERMISSION_MATRIX.find((item) => item.id === 'fabrica');
    expect(linha?.segmento).toBe('marcenaria');
  });

  it('não entra na conta do nível do cargo (o "Gestor" de hoje continua Gestor)', () => {
    expect(PERMISSION_KEYS).not.toContain('view_fabrica');
    expect(PERMISSION_KEYS).not.toContain('manage_fabrica');
    expect(ALL_PERMISSION_KEYS).toContain('manage_fabrica');
  });

  it('marcar uma caixa grava a chave genérica `fabrica`', () => {
    expect(applyEndpointPermissions({ view_fabrica: true }).fabrica).toBe(true);
    expect(applyEndpointPermissions({ view_fabrica: false, manage_fabrica: false }).fabrica).toBe(false);
  });
});
