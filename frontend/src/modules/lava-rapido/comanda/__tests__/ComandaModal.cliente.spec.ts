/**
 * Spec 03B — a comanda abre com o cliente escolhido na busca (padrão da OS).
 *
 * Bug relatado em 12/11: "selecionei o cliente e não apareceu". Monta a comanda
 * de verdade (useComanda real) com as consultas e os filhos pesados simulados.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

// --- Dados e consultas simulados --------------------------------------------------------
vi.mock('@/modules/order-service/shared/segmento/useTiposDeTrabalho', () => ({
  useTiposDeTrabalho: () => ({
    opcoes: ref([{ value: 'carro', label: 'Carro' }]),
    tipoPorId: () => ({ id: 'carro', label: 'Carro', campos: [{ nome: 'placa', obrigatorio: true }], avarias: [] }),
  }),
}));
vi.mock('../../shared/composables/usePortes', () => ({
  usePortesQuery: () => ({ data: ref([]), ativosDoTipo: () => [] }),
  useServicosDoPorteQuery: () => ({ data: ref([]), isLoading: ref(false) }),
}));
vi.mock('@/modules/order-service/ordens/composables/modal/useOSSelectOptions', () => ({
  useOSSelectOptions: () => ({ funcionariosOptions: ref([]), statusOptions: ref([]), prioridadeOptions: ref([]) }),
}));
vi.mock('@/shared/stores/auth.store', () => ({ useAuthStore: () => ({ userData: { funcionario_id: 1, cargo: null } }) }));
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
vi.mock('@/modules/order-service/ordens/services/orderServiceGet.service', () => ({ buscarObjetosPorIdentificador: vi.fn(async () => []) }));
vi.mock('@/modules/order-service/ordens/services/relationship/osRelationshipGet.service', () => ({ getCustomerByIdForOS: vi.fn() }));
vi.mock('../services/comanda.service', () => ({ abrirLavagem: vi.fn() }));

// --- Filhos pesados viram marcadores -------------------------------------------------------
const marcador = (nome: string, render?: (props: Record<string, unknown>) => unknown) => ({
  __esModule: true,
  default: defineComponent({
    name: nome,
    props: ['cliente', 'isOpen', 'item'],
    emits: ['select-cliente', 'selectCliente', 'close'],
    setup: (props) => () => h('div', { 'data-testid': nome }, render ? String(render(props)) : ''),
  }),
});
vi.mock('@/modules/order-service/ordens/components/form/OSClientCard.vue', () =>
  marcador('cartao-cliente', (p) => (p.cliente as { nome?: string } | null)?.nome ?? ''));
vi.mock('@/modules/order-service/ordens/components/form/OSControlsCard.vue', () => marcador('controles'));
vi.mock('@/modules/order-service/ordens/components/form/OSSummaryCard.vue', () => marcador('resumo'));
vi.mock('@/modules/order-service/ordens/components/form/OSItemFormModal.vue', () => marcador('item'));
vi.mock('@/modules/order-service/ordens/components/form/OSFotoGallery.vue', () => marcador('fotos'));
vi.mock('@/modules/order-service/ordens/components/OSClienteSearchModal.vue', () => marcador('busca'));
vi.mock('../../shared/components/SeletorLavadores.vue', () => marcador('lavadores'));

const { default: ComandaModal } = await import('../components/ComandaModal.vue');

const MARIA = { id: 7, tipo: 'PF', nome: 'Maria Cliente' };

describe('comanda com o cliente da busca', () => {
  it('abre já com o cliente escolhido', async () => {
    const w = mount(ComandaModal, { props: { isOpen: false, cliente: null }, attachTo: document.body });
    await w.setProps({ isOpen: true, cliente: MARIA as never });
    await flushPromises();
    expect(document.body.querySelector('[data-testid="cartao-cliente"]')?.textContent).toBe('Maria Cliente');
    w.unmount();
  });

  it('cliente e abertura chegando juntos no mesmo tique (como na entrada)', async () => {
    const w = mount(ComandaModal, { props: { isOpen: false, cliente: null }, attachTo: document.body });
    w.setProps({ cliente: MARIA as never });
    await w.setProps({ isOpen: true });
    await flushPromises();
    expect(document.body.querySelector('[data-testid="cartao-cliente"]')?.textContent).toBe('Maria Cliente');
    w.unmount();
  });

  it('"Selecionar cliente" de dentro da comanda mostra o escolhido', async () => {
    const w = mount(ComandaModal, { props: { isOpen: false, cliente: null }, attachTo: document.body });
    await w.setProps({ isOpen: true });
    await flushPromises();
    const busca = w.findComponent({ name: 'busca' });
    busca.vm.$emit('selectCliente', MARIA);
    busca.vm.$emit('close');
    await flushPromises();
    expect(document.body.querySelector('[data-testid="cartao-cliente"]')?.textContent).toBe('Maria Cliente');
    w.unmount();
  });

  it('comanda que já estava aberta recebe o cliente novo (tela trocada e devolvida)', async () => {
    const w = mount(ComandaModal, { props: { isOpen: true, cliente: null }, attachTo: document.body });
    await flushPromises();
    await w.setProps({ cliente: MARIA as never });
    await flushPromises();
    expect(document.body.querySelector('[data-testid="cartao-cliente"]')?.textContent).toBe('Maria Cliente');
    w.unmount();
  });
});
