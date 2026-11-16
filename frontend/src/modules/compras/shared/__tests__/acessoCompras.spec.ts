/**
 * Módulo de Compras no frontend: o que não pode regredir ao chegar nos clientes.
 *
 * 1. Licença sem resposta NÃO libera Compras (é pago à parte), mas continua
 *    liberando os módulos de sempre.
 * 2. A linha "Compras" da tela de Cargos não muda o NÍVEL de nenhum cargo que
 *    já existe (Administrador, Gestor...) — senão a atualização rebaixaria o
 *    "Gestor" de toda loja, inclusive das que nem contrataram o módulo.
 */
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it } from 'vitest';

import {
  ALL_PERMISSION_KEYS,
  PERMISSION_KEYS,
  applyEndpointPermissions,
  getAccessLevel,
  getPermissionStats,
} from '@/modules/employees/constants/positions.constants';
import { MODULOS } from '@/shared/constants/modulos.constants';
import { useModulosStore } from '@/shared/stores/modulos.store';

describe('trava do módulo COMPRAS', () => {
  beforeEach(() => setActivePinia(createPinia()));

  it('licença sem resposta (null ou vazia) não libera Compras', () => {
    const store = useModulosStore();
    expect(store.temModulo(MODULOS.COMPRAS)).toBe(false);
    store.definir([]);
    expect(store.temModulo(MODULOS.COMPRAS)).toBe(false);
  });

  it('licença sem resposta continua liberando o Financeiro de sempre', () => {
    const store = useModulosStore();
    store.definir([]);
    expect(store.temModulo(MODULOS.FINANCEIRO)).toBe(true);
  });

  it('libera só quando a licença traz COMPRAS', () => {
    const store = useModulosStore();
    store.definir([MODULOS.FINANCEIRO]);
    expect(store.temModulo(MODULOS.COMPRAS)).toBe(false);
    store.definir([MODULOS.FINANCEIRO, MODULOS.COMPRAS]);
    expect(store.temModulo(MODULOS.COMPRAS)).toBe(true);
  });
});

describe('linha "Compras" na tela de Cargos', () => {
  it('não entra na conta do nível do cargo', () => {
    expect(PERMISSION_KEYS).not.toContain('view_purchases');
    expect(PERMISSION_KEYS).not.toContain('manage_purchases');
    expect(PERMISSION_KEYS).not.toContain('delete_purchases');
    expect(ALL_PERMISSION_KEYS).toEqual(
      expect.arrayContaining(['view_purchases', 'manage_purchases', 'delete_purchases']),
    );
  });

  it('um cargo existente mantém o nível de antes', () => {
    // Um cargo com todas as caixas de sempre e nenhuma de Compras continua Administrador.
    const todasDeSempre = Object.fromEntries(PERMISSION_KEYS.map((k) => [k, true]));
    expect(getPermissionStats(todasDeSempre).ratio).toBe(1);
    expect(getAccessLevel(todasDeSempre).id).toBe('administrator');
  });

  it('marcar uma caixa de Compras grava também a chave do módulo (`compra`)', () => {
    expect(applyEndpointPermissions({ view_purchases: true }).compra).toBe(true);
    expect(applyEndpointPermissions({ view_purchases: false, manage_purchases: false }).compra).toBe(false);
  });

  it('a linha Recebimento fica fora do nível e grava a PRÓPRIA chave', () => {
    expect(PERMISSION_KEYS).not.toContain('receive_purchases');
    expect(PERMISSION_KEYS).not.toContain('view_receiving');
    // Só recebimento: liga `recebimento_compra` e NÃO liga `compra` (que daria
    // ao almoxarife o que a linha Compras libera, inclusive ver preço).
    const almoxarife = applyEndpointPermissions({ view_receiving: true, receive_purchases: true });
    expect(almoxarife.recebimento_compra).toBe(true);
    expect(almoxarife.compra).toBe(false);
    // E as duas linhas juntas não se sobrescrevem.
    const comprador = applyEndpointPermissions({ manage_purchases: true, receive_purchases: true });
    expect([comprador.compra, comprador.recebimento_compra]).toEqual([true, true]);
  });
});
