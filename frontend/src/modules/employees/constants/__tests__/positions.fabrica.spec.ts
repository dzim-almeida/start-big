/**
 * Spec 03B (marcenaria, D12) — a linha "Fábrica" saiu da tela de Cargos.
 *
 * O que não pode regredir: a linha era só da marcenaria e não entrava na
 * conta do nível do cargo. Tirá-la não pode mudar o nível de NENHUM cargo de
 * nenhum segmento. Os retratos em __snapshots__ foram gerados com o código de
 * ANTES da mudança.
 */
import { describe, expect, it } from 'vitest';

import {
  ALL_PERMISSION_KEYS,
  PERMISSION_KEYS,
  PERMISSION_MATRIX,
  getAccessLevel,
} from '@/modules/employees/constants/positions.constants';

/** Cargos de exemplo: todas as caixas, metade, só visualizar, nenhuma, e um com a Fábrica marcada. */
function cargosDeExemplo(): Record<string, Record<string, boolean>> {
  const todas = Object.fromEntries(PERMISSION_KEYS.map((k) => [k, true]));
  const metade = Object.fromEntries(PERMISSION_KEYS.map((k, i) => [k, i % 2 === 0]));
  const soVer = Object.fromEntries(PERMISSION_KEYS.map((k) => [k, k.startsWith('view_')]));
  return {
    todas,
    metade,
    soVer,
    nenhuma: {},
    // Cargo que JÁ gravou as chaves da fábrica: continua com elas, sem efeito.
    comFabricaGravada: { ...metade, view_fabrica: true, manage_fabrica: true },
  };
}

describe('linha "Fábrica" de Cargos (aposentada)', () => {
  it('20 — não existe mais na matriz', () => {
    expect(PERMISSION_MATRIX.find((item) => item.id === 'fabrica')).toBeUndefined();
    expect(ALL_PERMISSION_KEYS).not.toContain('view_fabrica');
    expect(ALL_PERMISSION_KEYS).not.toContain('manage_fabrica');
  });

  it('20 — PERMISSION_KEYS igual ao de antes (a linha nunca contou no nível)', () => {
    expect(PERMISSION_KEYS).toMatchSnapshot();
  });

  it('o nível de acesso dos cargos de exemplo é o mesmo de antes', () => {
    const niveis = Object.fromEntries(
      Object.entries(cargosDeExemplo()).map(([nome, permissoes]) => [nome, getAccessLevel(permissoes).label]),
    );
    expect(niveis).toMatchSnapshot();
  });
});
