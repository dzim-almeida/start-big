/**
 * CT-17 (LIC-04): o `useUserQuery` só busca o usuário quando há token na
 * sessão da janela (sessionStorage), lido pelo tokenSessao.service.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';
import { mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';

// Simula a chamada ao backend: só queremos saber SE ela foi feita.
const getUser = vi.fn().mockResolvedValue({ id: 1 });
vi.mock('../../services/user.service', () => ({ getUser: () => getUser() }));

import { useUserQuery } from '../useUser';

/** Monta um componente mínimo que usa o composable (ele precisa do vue-query). */
function montar() {
  const Componente = defineComponent({
    setup() {
      useUserQuery();
      return () => h('div');
    },
  });
  // QueryClient novo por teste, sem tentar de novo, para o cache não vazar
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return mount(Componente, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } });
}

afterEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  getUser.mockClear();
});

describe('useUserQuery', () => {
  it('CT-17: com token na sessionStorage, busca o usuário', async () => {
    sessionStorage.setItem('access_token', 'abc');
    montar();
    await vi.waitFor(() => expect(getUser).toHaveBeenCalled());
  });

  it('sem token, não busca (token antigo no localStorage não conta)', async () => {
    localStorage.setItem('access_token', 'de-versao-antiga');
    montar();
    await new Promise((r) => setTimeout(r, 20)); // dá tempo de uma busca acontecer, se fosse acontecer
    expect(getUser).not.toHaveBeenCalled();
  });
});
