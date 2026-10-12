/**
 * Spec 04B (marcenaria, D2/D6) — a capacidade `orcamento_tecnico` durante o
 * carregamento (caso 10) e a query da seção, que fora da marcenaria nem é
 * chamada (caso 17: a rota responderia 404).
 */
import { mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

const carregando = ref(true);                     // contrato do segmento ainda carregando?
const segmentoAtual = ref<string | null>(null);
const buscar = vi.fn(async () => ({}));           // a chamada GET /configuracoes/marcenaria

vi.mock('@/modules/order-service/shared/segmento/useOSFieldDefinition.queries', () => ({
  useOSFieldDefinition: () => ({ data: ref(undefined), isPending: carregando }),
}));
vi.mock('@/shared/composables/useSegmento', () => ({
  useSegmento: () => ({ segmento: segmentoAtual }),
}));
vi.mock('../../../../services/configuracaoMarcenaria.service', () => ({
  getConfiguracaoMarcenaria: () => buscar(),
}));

const { useCapacidades } = await import('@/modules/order-service/shared/segmento/useCapacidades');

describe('capacidade durante o carregamento', () => {
  it('10 — marcenaria, contrato carregando: temOrcamentoTecnico já é true (fallback)', () => {
    carregando.value = true;
    segmentoAtual.value = 'marcenaria';
    expect(useCapacidades().temOrcamentoTecnico.value).toBe(true);
  });

  it('informática, contrato carregando: false', () => {
    carregando.value = true;
    segmentoAtual.value = 'assistencia_tecnica';
    expect(useCapacidades().temOrcamentoTecnico.value).toBe(false);
  });
});

describe('query da seção Marcenaria', () => {
  /** Monta um componente mínimo que usa a query, com o capacidade simulada. */
  async function usarQuery(temCapacidade: boolean) {
    vi.resetModules();                                    // recarrega com o mock novo
    const temOrcamentoTecnico = ref(temCapacidade);       // valor novo a cada montagem
    vi.doMock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
      useCapacidades: () => ({ temOrcamentoTecnico }),
    }));
    const { useConfiguracaoMarcenariaQuery } = await import('../../../../composables/queries/useConfiguracaoMarcenariaQuery');
    const Teste = defineComponent({ setup: () => { useConfiguracaoMarcenariaQuery(); return () => h('div'); } });
    const wrapper = mount(Teste, { global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] } });
    await new Promise((r) => setTimeout(r, 0));          // dá tempo de a query disparar
    wrapper.unmount();                                    // não deixa a query viva para o próximo teste
  }

  it('17 — sem a capacidade (informática): a rota nem é chamada', async () => {
    buscar.mockClear();
    await usarQuery(false);
    expect(buscar).not.toHaveBeenCalled();
  });

  it('com a capacidade (marcenaria): busca os parâmetros', async () => {
    buscar.mockClear();
    await usarQuery(true);
    expect(buscar).toHaveBeenCalledTimes(1);
  });
});
