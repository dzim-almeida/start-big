/**
 * ⚠️ Código compartilhado da OS — "Adicionar Item" com serviço digitado à mão.
 *
 * Ligado por padrão em todos os segmentos: confere se o serviço existe; se não,
 * pergunta se salva no cadastro. Com `oferecerCadastroServico=false`, o modal
 * não consulta nada e emite como antes.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { computed, defineComponent, h } from 'vue';

const getServicos = vi.fn();
const createServico = vi.fn();
vi.mock('@/modules/order-service/servicos/services/servicos.service', () => ({
  getServicos: (...a: unknown[]) => getServicos(...a),
  createServico: (...a: unknown[]) => createServico(...a),
}));
vi.mock('@/modules/products/inventory/composables/useProductsQuery', () => ({
  useProductsQuery: () => ({ data: computed(() => []), isLoading: computed(() => false) }),
}));
vi.mock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
  useCapacidades: () => ({ temAprovacaoItens: computed(() => false), temGarantiaItens: computed(() => false) }),
}));
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
// Modal simples: mostra corpo e rodapé quando aberto (sem Teleport).
vi.mock('@/shared/components/commons/BaseModal/BaseModal.vue', () => ({
  __esModule: true,
  default: defineComponent({
    props: { isOpen: Boolean, title: String },
    setup(props, { slots }) {
      return () => (props.isOpen
        ? h('section', { 'data-titulo': props.title }, [slots.default?.(), slots.footer?.()])
        : null);
    },
  }),
}));

const { default: OSItemFormModal } = await import('../OSItemFormModal.vue');

function montar(oferecer?: boolean) {
  const w = mount(OSItemFormModal, {
    props: { isOpen: false, ...(oferecer === undefined ? {} : { oferecerCadastroServico: oferecer }) },
    global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
  });
  return w;
}

async function preencherEAdicionar(w: ReturnType<typeof montar>, nome: string, valor: number) {
  await w.setProps({ isOpen: true });
  const vm = w.vm as unknown as { nome: string; valorUnitarioNum: number };
  vm.nome = nome;
  vm.valorUnitarioNum = valor;
  await flushPromises();
  const botao = w.findAll('button').find((b) => b.text().includes('ADICIONAR ITEM'))!;
  await botao.trigger('click');
  await flushPromises();
}

const botaoComTexto = (w: ReturnType<typeof montar>, texto: string) =>
  w.findAll('button').find((b) => b.text().includes(texto))!;

describe('OSItemFormModal — cadastro do serviço digitado à mão', () => {
  beforeEach(() => {
    getServicos.mockReset();
    createServico.mockReset();
  });

  it('desligado (false): não consulta o cadastro e emite como antes', async () => {
    const w = montar(false);
    await preencherEAdicionar(w, 'Polimento', 120);
    expect(getServicos).not.toHaveBeenCalled();
    const item = w.emitted('save')![0][0] as Record<string, unknown>;
    expect(item.nome).toBe('Polimento');
    expect(item).not.toHaveProperty('item_id');
  });

  it('já cadastrado (sem ligar para acento e caixa): liga a linha a ele, sem perguntar', async () => {
    getServicos.mockResolvedValue({ items: [{ id: 7, descricao: 'Higienização Interna', valor: 15000 }] });
    const w = montar(true);
    await preencherEAdicionar(w, 'higienizacao  interna', 150);
    expect(w.find('[data-titulo="Serviço não cadastrado"]').exists()).toBe(false);
    expect((w.emitted('save')![0][0] as Record<string, unknown>).item_id).toBe(7);
  });

  it('não cadastrado: pergunta; "Salvar no cadastro" cria e liga o item', async () => {
    getServicos.mockResolvedValue({ items: [] });
    createServico.mockResolvedValue({ id: 42, descricao: 'Polimento', valor: 12000 });
    const w = montar(true);
    await preencherEAdicionar(w, 'Polimento', 120);
    expect(w.emitted('save')).toBeUndefined();
    expect(w.find('[data-titulo="Serviço não cadastrado"]').exists()).toBe(true);

    await botaoComTexto(w, 'Salvar no cadastro').trigger('click');
    await flushPromises();
    expect(createServico).toHaveBeenCalledWith({ descricao: 'Polimento', valor: 12000 });
    expect((w.emitted('save')![0][0] as Record<string, unknown>).item_id).toBe(42);
  });

  it('não cadastrado: "Só nesta OS" emite como avulso, sem criar', async () => {
    getServicos.mockResolvedValue({ items: [] });
    const w = montar(true);
    await preencherEAdicionar(w, 'Polimento', 120);
    await botaoComTexto(w, 'Só nesta OS').trigger('click');
    await flushPromises();
    expect(createServico).not.toHaveBeenCalled();
    expect(w.emitted('save')![0][0]).not.toHaveProperty('item_id');
  });

  it('padrão (sem passar a opção, como no formulário da OS): confere e pergunta', async () => {
    getServicos.mockResolvedValue({ items: [] });
    const w = montar();
    await preencherEAdicionar(w, 'Troca de tela', 300);
    expect(getServicos).toHaveBeenCalled();
    expect(w.find('[data-titulo="Serviço não cadastrado"]').exists()).toBe(true);
  });

  it('produto digitado à mão não passa pela conferência de serviço', async () => {
    const w = montar();
    await w.setProps({ isOpen: true });
    const vm = w.vm as unknown as { tipo: string; nome: string };
    vm.tipo = 'PRODUTO';
    await flushPromises();
    vm.nome = 'Cera avulsa';
    await flushPromises();
    await w.findAll('button').find((b) => b.text().includes('ADICIONAR ITEM'))!.trigger('click');
    await flushPromises();
    expect(getServicos).not.toHaveBeenCalled();
    expect(w.emitted('save')).toHaveLength(1);
  });

  it('editar um item avulso não pergunta de novo', async () => {
    const w = mount(OSItemFormModal, {
      props: {
        isOpen: false,
        item: { tipo: 'SERVICO', nome: 'Polimento', unidade_medida: 'UN', quantidade: 1, valor_unitario: 12000 } as never,
      },
      global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
    });
    await w.setProps({ isOpen: true });
    await flushPromises();
    await w.findAll('button').find((b) => b.text().includes('SALVAR ALTERAÇÕES'))!.trigger('click');
    await flushPromises();
    expect(getServicos).not.toHaveBeenCalled();
    expect(w.emitted('save')).toHaveLength(1);
  });

  it('falha ao conferir: o item entra como avulso, como sempre entrou', async () => {
    getServicos.mockRejectedValue(new Error('rede'));
    const w = montar(true);
    await preencherEAdicionar(w, 'Polimento', 120);
    expect(w.emitted('save')).toHaveLength(1);
  });
});
