/**
 * Spec 06B — o editor inteiro montado pela ROTA (view + blocos), com a API
 * simulada pelos JSON reais do cenário B.
 *
 * - com custos: painel de custos e números do resumo;
 * - sem custos: nada de custo na tela (D16);
 * - caso 13: "/orcamentos/novo" não grava nada até a primeira informação real;
 *   escolher o cliente faz o POST e troca a rota SEM recomeçar o editor (D5).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';
import { createMemoryHistory, createRouter, RouterView } from 'vue-router';

// O que o GET devolve. Variável comum (não `ref`): um Proxy reativo não passa pelo structuredClone.
const resposta: { detalhe: unknown } = { detalhe: null };
const criar = vi.fn();
const patch = vi.fn();

vi.mock('../services/orcamento.service', () => ({
  URL_ORCAMENTOS: '/marcenaria/orcamentos',
  getOrcamento: async () => structuredClone(resposta.detalhe),
  getVersoes: async () => [],
  getHistorico: async () => [],
  getProjetosDoCliente: async () => [],
  getArquitetos: async () => [{ id: 1, nome: 'Studio Renascer', nome_fantasia: null }],   // Spec 09B
  criarOrcamento: (...args: unknown[]) => criar(...args),
  patchOrcamento: (...args: unknown[]) => patch(...args),
}));
vi.mock('../services/orcamentoAnexos.service', () => ({ listarAnexos: async () => [] }));
vi.mock('../services/aprovacao.service', async (original) => ({
  ...(await original<typeof import('../services/aprovacao.service')>()),
  getResumoPorOs: async () => (await import('./fixtures/resumo-por-os.json')).default,
}));
vi.mock('@/modules/order-service/ordens/composables/request/relationship/useOSRelationshipGet.queries', () => ({
  useOsEmployeesGet: () => ({ data: ref([{ id: 1, nome: 'Admin Master' }]), isError: ref(false) }),
}));
vi.mock('@/modules/order-service/shared/segmento/useOSFieldDefinition.queries', () => ({
  useOSFieldDefinition: () => ({ data: ref(undefined), isPending: ref(false) }),
}));
vi.mock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
  useCapacidades: () => ({ tem: () => true, temOrcamentoTecnico: ref(true) }),
}));
vi.mock('@/shared/stores/auth.store', () => ({
  useAuthStore: () => ({ userData: ref({ is_master: true, funcionario_id: 1 }) }),
}));
// A busca de cliente da OS é outra tela: aqui, um botão que "escolhe" o cliente 5.
vi.mock('@/modules/order-service/ordens/components/OSClienteSearchModal.vue', () => ({
  default: defineComponent({
    props: ['isOpen'],
    emits: ['selectCliente', 'selectObjeto', 'close'],
    setup: (_p, { emit }) => () => h('button', {
      'data-testid': 'simular-escolha-cliente',
      onClick: () => emit('selectCliente', { id: 5, tipo: 'PF', nome: 'Dona Marta' }),
    }),
  }),
}));

const { default: OrcamentoEditorView } = await import('../views/OrcamentoEditorView.vue');
const { default: EditorOrcamento } = await import('../components/editor/EditorOrcamento.vue');
const { detalheFixture, novoQueryClient } = await import('./apoio');
const { orcamentoDetalheSchema } = await import('../schemas/orcamentoDetalhe.schema');
const aprovadoFixture = (await import('./fixtures/detalhe-aprovado-com-custos.json')).default;

function montarNaRota(caminho: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { render: () => h('div') } },
      { path: '/orcamentos', name: 'marcenaria-orcamentos', component: { render: () => h('div', 'lista') } },
      { path: '/orcamentos/novo', name: 'marcenaria-orcamento-novo', component: OrcamentoEditorView },
      { path: '/orcamentos/:id(\\d+)', name: 'marcenaria-orcamento', component: OrcamentoEditorView, props: (r) => ({ id: Number(r.params.id) }) },
    ],
  });
  const App = defineComponent({ setup: () => () => h(RouterView) });
  return {
    router,
    async montar() {
      await router.push(caminho);
      const wrapper = mount(App, {
        attachTo: document.body,
        global: { plugins: [router, [VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never, directives: { maska: {} } },
      });
      await flushPromises();
      // A query do detalhe responde num ciclo seguinte: espera o código aparecer (ou o "novo").
      await vi.waitFor(() => {
        if (!/ORC-|Novo orçamento$/.test(wrapper.find('[data-testid="codigo-orcamento"]').text())) throw new Error('carregando');
        if (wrapper.text().includes('Carregando orçamento')) throw new Error('carregando');
      });
      return wrapper;
    },
  };
}

beforeEach(() => { criar.mockReset(); patch.mockReset(); });
afterEach(() => { vi.useRealTimers(); document.body.innerHTML = ''; });

describe('editor do orçamento (pela rota)', () => {
  it('com custos: blocos, resumo do cenário B e painel de custos', async () => {
    resposta.detalhe = detalheFixture(true);
    const wrapper = await montarNaRota('/orcamentos/1').montar();
    const texto = wrapper.text();
    expect(texto).toContain('ORC-2026-000001');
    expect(texto).toContain('Cozinha Gourmet');
    expect(texto).toContain('Torre Quente');
    expect(wrapper.find('[data-testid="total"]').text()).toBe('R$ 9.238,89');
    expect(wrapper.find('[data-testid="painel-custos"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="acao-enviar"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="acao-excluir"]').exists()).toBe(false);   // escondido no "Mais"
  });

  it('sem custos (D16): sem painel de custos, instalação só com o preço', async () => {
    resposta.detalhe = detalheFixture(false);
    const wrapper = await montarNaRota('/orcamentos/1').montar();
    expect(wrapper.find('[data-testid="painel-custos"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="instalacao-so-preco"]').text()).toContain('R$ 1.425,00');
    expect(wrapper.findAll('[data-testid="custo-movel"]')).toHaveLength(0);
  });

  it('aprovado (08B): faixa com a OS, móvel recusado esmaecido, resumo proposto × aprovado, nada editável', async () => {
    resposta.detalhe = orcamentoDetalheSchema.parse(structuredClone(aprovadoFixture));
    const wrapper = await montarNaRota('/orcamentos/1').montar();
    await vi.waitFor(() => expect(wrapper.find('[data-testid="faixa-texto"]').text()).toContain('por Admin Master'));
    expect(wrapper.find('[data-testid="faixa-texto"]').text()).toContain('OS-2026-000001');
    expect(wrapper.find('[data-testid="acao-desfazer"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="movel-2"] [data-testid="selo-nao-aprovado"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="painel-resumo"]').text()).toContain('Aprovado');
    expect(wrapper.find('[data-testid="acao-aprovar"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="novo-ambiente"]').exists()).toBe(false);
  });

  it('13 — "novo": nada é gravado até escolher o cliente; aí POST e a rota vira /orcamentos/:id', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] });
    resposta.detalhe = detalheFixture(true);
    criar.mockImplementation(async () => detalheFixture(true));        // o servidor cria o id 1
    const rota = montarNaRota('/orcamentos/novo');
    const wrapper = await rota.montar();
    expect(wrapper.find('[data-testid="codigo-orcamento"]').text()).toBe('Novo orçamento');

    await vi.advanceTimersByTimeAsync(5000);
    expect(criar).not.toHaveBeenCalled();                               // abrir e esperar não cria nada (D5)

    const editorAntes = wrapper.findComponent(EditorOrcamento).vm.$.uid;
    await wrapper.find('[data-testid="simular-escolha-cliente"]').trigger('click');
    await vi.advanceTimersByTimeAsync(900);                             // os 800 ms do salvamento
    await flushPromises();
    expect(criar).toHaveBeenCalledTimes(1);
    expect(criar.mock.calls[0][0]).toMatchObject({ cliente_id: 5 });
    expect(patch).not.toHaveBeenCalled();
    expect(rota.router.currentRoute.value.fullPath).toBe('/orcamentos/1');
    expect(wrapper.findComponent(EditorOrcamento).vm.$.uid).toBe(editorAntes);   // o MESMO editor continua
    expect(wrapper.find('[data-testid="codigo-orcamento"]').text()).toBe('ORC-2026-000001');
  });
});
