/**
 * Testes das rotas /sign-in e /login (bug do build de teste, 11/2026).
 *
 * O bug: depois do re-login sem backup, recarregar a tela no meio do setup
 * abria o login e não saía mais. A rota decidia por "tem licença", e depois
 * do re-login a licença já existe, mas o usuário Master ainda não.
 *
 * Agora as duas rotas perguntam "o setup terminou?" (GET /auth/status).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { RouteRecordRaw } from 'vue-router';

// A resposta do backend é simulada: nenhum teste fala com a rede.
const sistemaFoiConfigurado = vi.fn<() => Promise<boolean | null>>();
vi.mock('@/shared/services/sistema.service', () => ({
  sistemaFoiConfigurado: () => sistemaFoiConfigurado(),
}));

import rotasSignIn from '../routes';
import rotasAuth from '@/modules/auth/routes';

/** Roda o `beforeEnter` de uma rota e devolve para onde ela mandou (undefined = deixou entrar). */
async function entrar(rota: RouteRecordRaw) {
  const guarda = rota.beforeEnter as unknown as () => Promise<unknown>;
  return guarda();
}

const signIn = rotasSignIn[0];
const login = rotasAuth[0];

describe('rota /sign-in', () => {
  beforeEach(() => sistemaFoiConfigurado.mockReset());

  it('setup interrompido (licença salva, sem Master): fica no sign-in', async () => {
    sistemaFoiConfigurado.mockResolvedValue(false);
    expect(await entrar(signIn)).toBeUndefined();
  });

  it('setup feito: manda para o login', async () => {
    sistemaFoiConfigurado.mockResolvedValue(true);
    expect(await entrar(signIn)).toEqual({ name: 'auth.user' });
  });

  it('sem resposta do backend: fica no sign-in, como antes', async () => {
    sistemaFoiConfigurado.mockResolvedValue(null);
    expect(await entrar(signIn)).toBeUndefined();
  });
});

describe('rota /login', () => {
  beforeEach(() => sistemaFoiConfigurado.mockReset());

  it('sem setup não há usuário para entrar: volta para o sign-in', async () => {
    sistemaFoiConfigurado.mockResolvedValue(false);
    expect(await entrar(login)).toEqual({ name: 'sign-in' });
  });

  it('setup feito: mostra o login', async () => {
    sistemaFoiConfigurado.mockResolvedValue(true);
    expect(await entrar(login)).toBeUndefined();
  });

  it('sem resposta do backend: mostra o login, como antes', async () => {
    sistemaFoiConfigurado.mockResolvedValue(null);
    expect(await entrar(login)).toBeUndefined();
  });
});
