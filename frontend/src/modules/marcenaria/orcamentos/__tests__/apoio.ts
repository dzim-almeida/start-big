/**
 * Ajudantes dos testes do orçamento de marcenaria (Spec 06B §11).
 *
 * - `montarComposable`: roda um composable dentro de um componente de verdade,
 *   com o TanStack Query instalado (a fila e as queries precisam dele).
 * - `detalheFixture`: o detalhe REAL da API (cenário B), com ou sem custos.
 * - `erroApi` / `erroRede`: erros no formato do axios, como a API devolve.
 */
import { mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios';
import { defineComponent, h } from 'vue';

import { orcamentoDetalheSchema, type OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import comCustos from './fixtures/detalhe-com-custos.json';
import semCustos from './fixtures/detalhe-sem-custos.json';

/** Um QueryClient de teste: sem novas tentativas e sem cache entre testes. */
export function novoQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
}

/** Executa `usar()` no setup de um componente montado; devolve o resultado. */
export function montarComposable<T>(usar: () => T, queryClient: QueryClient = novoQueryClient()) {
  let resultado!: T;
  const Teste = defineComponent({
    setup() {
      resultado = usar();
      return () => h('div');
    },
  });
  const wrapper = mount(Teste, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } });
  return { resultado, queryClient, wrapper };
}

/** Detalhe real da API (cópia nova a cada chamada). */
export function detalheFixture(incluiCustos = true): OrcamentoDetalhe {
  return orcamentoDetalheSchema.parse(structuredClone(incluiCustos ? comCustos : semCustos));
}

/** Erro com resposta do servidor (409, 422...). */
export function erroApi(status: number, detail: unknown): AxiosError {
  const resposta = { status, data: { detail }, statusText: '', headers: {}, config: { headers: new AxiosHeaders() } } as AxiosResponse;
  return new AxiosError('erro', 'ERR_BAD_RESPONSE', undefined, undefined, resposta);
}

/** Erro de rede: sem resposta (vale tentar de novo, D9). */
export function erroRede(): AxiosError {
  return new AxiosError('Network Error', 'ERR_NETWORK');
}
