/**
 * Spec 06B §11 — casos 19 a 22: modal do móvel, busca de insumo e cadastro
 * rápido. Os serviços (simular, fornecedores, produtos) são SIMULADOS.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

const simular = vi.fn(async () => ({ calculo: { preco_unit_centavos: 100, preco_total_centavos: 100 }, insumos: [], avisos: [] }));
const criarProduto = vi.fn();
const buscarProdutos = vi.fn();

vi.mock('../services/orcamentoMovel.service', () => ({ simularMovel: () => simular() }));
vi.mock('@/modules/products/suppliers/services/fornecedor.service', () => ({
  getFornecedores: async () => [{ id: 2, nome: 'Madeiranit', ativo: true }],
}));
vi.mock('@/modules/products/inventory/services/product.service', () => ({
  createProduto: (...args: unknown[]) => criarProduto(...args),
  getProdutos: (...args: unknown[]) => buscarProdutos(...args),
}));

const { default: MovelModal } = await import('../components/modais/MovelModal.vue');
const { default: InsumoBusca } = await import('../components/modais/InsumoBusca.vue');
const { default: InsumosEditor } = await import('../components/modais/InsumosEditor.vue');
const { default: InsumoRapidoModal } = await import('../components/modais/InsumoRapidoModal.vue');
const { movelFormSchema, movelParaForm, movelVazio, paraApiMovel } = await import('../schemas/movelForm.schema');
const { detalheFixture, novoQueryClient } = await import('./apoio');

afterEach(() => {
  document.body.innerHTML = '';
  vi.clearAllMocks();
});

const plugins = () => [[VueQueryPlugin, { queryClient: novoQueryClient() }] as const, createPinia()];
/** O BaseInput usa a diretiva de máscara registrada no main.ts: aqui, uma vazia. */
const directives = { maska: {} };

/** Abre o modal do móvel; `salvar` registra o que o editor receberia. */
function abrirModal(props: Record<string, unknown>) {
  const salvar = vi.fn(async () => true);
  mount(MovelModal, {
    props: {
      isOpen: true, orcamentoId: 1, ambienteId: 1, ambientes: [{ id: 1, nome: 'Cozinha Gourmet' }],
      custoHoraCentavos: 4500, editavel: true, podeCadastrarInsumo: false, incluiCustos: false, salvar, ...props,
    },
    global: { plugins: plugins() as never, directives },
    attachTo: document.body,
  });
  return { salvar };
}
const clicar = async (testid: string) => {
  (document.querySelector(`[data-testid="${testid}"]`) as HTMLElement).click();
  await flushPromises();
};

describe('MovelModal', () => {
  it('19 — sem custos: sem mão de obra, central e custo; o envio não traz essas chaves', async () => {
    const movel = detalheFixture(false).ambientes[0].moveis[0];        // Torre Quente, terceirizada
    const { salvar } = abrirModal({ movel, incluiCustos: false, custoHoraCentavos: null });
    await flushPromises();
    expect(document.querySelector('[data-testid="mao-obra"]')).toBeNull();
    expect(document.querySelector('[data-testid="valor-central"]')).toBeNull();
    expect(document.querySelector('[data-testid="custo-insumo"]')).toBeNull();
    expect(document.querySelector('[data-testid="frase-sem-custos"]')).not.toBeNull();

    await clicar('salvar-movel');
    expect(salvar).toHaveBeenCalledTimes(1);
    const enviado = (salvar.mock.calls[0] as unknown as [{ movel: Record<string, unknown> & { insumos: Record<string, unknown>[] } }])[0].movel;
    expect('mao_obra' in enviado).toBe(false);                          // D24a: o backend mantém o do dono
    expect('terceirizado_centavos' in enviado).toBe(false);
    expect(enviado.insumos.every((i) => !('custo_unit_centavos' in i))).toBe(true);
    expect(enviado.insumos.every((i) => typeof i.id === 'number')).toBe(true);   // gravados vão com id
  });

  it('com custos: mão de obra e valor da central aparecem', async () => {
    const movel = detalheFixture(true).ambientes[0].moveis[0];
    abrirModal({ movel, incluiCustos: true });
    await flushPromises();
    expect(document.querySelector('[data-testid="mao-obra"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="valor-central"]')).not.toBeNull();
  });

  it('20 — terceirizada sem central: erro e nada é salvo', async () => {
    const { salvar } = abrirModal({ incluiCustos: true });
    await flushPromises();
    const nome = document.querySelector('[data-testid="movel-nome"] input, input[data-testid="movel-nome"]') as HTMLInputElement
      ?? document.querySelector('input') as HTMLInputElement;
    nome.value = 'Balcão';
    nome.dispatchEvent(new Event('input'));
    (document.querySelector('[data-testid="producao-terceirizada"]') as HTMLInputElement).click();
    await flushPromises();
    await clicar('salvar-movel');
    expect(salvar).not.toHaveBeenCalled();
    expect(document.querySelector('[data-testid="erro-central"]')?.textContent).toContain(
      'Móvel terceirizado precisa da central parceira.',
    );
  });
});

describe('formulário do móvel (regras do backend)', () => {
  it('central obrigatória em terceirizada; medidas inteiras de 1 mm a 100 m', () => {
    const base = { ...movelVazio(1), nome: 'Torre' };
    expect(movelFormSchema.safeParse({ ...base, tipo_producao: 'TERCEIRIZADA' }).success).toBe(false);
    expect(movelFormSchema.safeParse({ ...base, tipo_producao: 'TERCEIRIZADA', central_fornecedor_id: 2 }).success).toBe(true);
    expect(movelFormSchema.safeParse({ ...base, largura_mm: 0 }).success).toBe(false);
    expect(movelFormSchema.safeParse({ ...base, largura_mm: 700.5 }).success).toBe(false);
    expect(movelFormSchema.safeParse({ ...base, nome: '   ' }).success).toBe(false);
  });

  it('ida e volta: móvel gravado → formulário → API com custos', () => {
    const movel = detalheFixture(true).ambientes[0].moveis[0];
    const corpo = paraApiMovel(movelParaForm(movel), true);
    expect(corpo.mao_obra).toEqual({ modo: 'FIXA', centavos: 30000, horas_centesimos: 0 });
    expect(corpo.terceirizado_centavos).toBe(38000);
    expect(corpo.insumos[0]).toEqual({ id: 1, quantidade_milesimos: 1400 });   // custo copiado fica no servidor
  });
});

describe('21 — insumo que já está no móvel', () => {
  it('a busca avisa "existente" em vez de incluir de novo', async () => {
    buscarProdutos.mockResolvedValue([{ id: 7, nome: 'MDF Branco', codigo_produto: 'P-7', unidade_medida: 'UN', sofre_perda: true, estoque: { valor_varejo: 0, valor_entrada: 28000 } }]);
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    const w = mount(InsumoBusca, {
      props: { produtosNoMovel: [7], incluiCustos: true, podeCadastrar: false },
      global: { plugins: plugins() as never },
    });
    await w.find('[data-testid="busca-insumo"]').setValue('MDF');
    await vi.advanceTimersByTimeAsync(350);                            // 300 ms de espera da busca
    vi.useRealTimers();
    await flushPromises();
    await w.find('[data-testid="resultado-7"]').trigger('click');
    expect(w.emitted('existente')).toEqual([[7]]);
    expect(w.emitted('escolher')).toBeUndefined();
  });

  it('o editor foca a quantidade da linha existente e não cria linha nova', async () => {
    const insumos = ref(movelParaForm(detalheFixture(true).ambientes[0].moveis[0]).insumos);
    const Pai = defineComponent({
      setup: () => () => h(InsumosEditor, {
        modelValue: insumos.value, 'onUpdate:modelValue': (v: typeof insumos.value) => { insumos.value = v; },
        incluiCustos: true, editavel: true, podeCadastrar: false, erros: {},
      }),
    });
    const w = mount(Pai, { attachTo: document.body, global: { plugins: plugins() as never } });
    const antes = insumos.value.length;
    w.findComponent(InsumoBusca).vm.$emit('existente', 3);              // a Fita PVC já está no móvel
    await flushPromises();
    expect(insumos.value.length).toBe(antes);
    expect(document.activeElement?.getAttribute('data-testid')).toBe('quantidade-3');
  });
});

describe('22 — InsumoRapidoModal', () => {
  it('preço de venda vazio grava valor_varejo = custo no POST /produtos', async () => {
    criarProduto.mockResolvedValue({ id: 99, nome: 'Puxador', codigo_produto: 'INS-1', estoque: { valor_varejo: 1250 } });
    const w = mount(InsumoRapidoModal, {
      props: { isOpen: false, nomeInicial: 'Puxador' },
      global: { plugins: plugins() as never, directives },
      attachTo: document.body,
    });
    await w.setProps({ isOpen: true });                                // abrir preenche o formulário
    await flushPromises();
    // Custo de compra R$ 12,50 (o campo de dinheiro é o 1º MoneyInput do modal).
    const vm = w.vm as unknown as { $: { setupState: { form: { custo_reais: number } } } };
    vm.$.setupState.form.custo_reais = 12.5;
    await flushPromises();
    await clicar('salvar-insumo-rapido');
    expect(criarProduto).toHaveBeenCalledTimes(1);
    const corpo = criarProduto.mock.calls[0][0] as { estoque: { valor_varejo: number; valor_entrada: number; quantidade: number }; nome: string };
    expect(corpo.nome).toBe('Puxador');
    expect(corpo.estoque).toEqual({ quantidade: 0, valor_entrada: 1250, valor_varejo: 1250 });
    expect(w.emitted('criado')?.[0]?.[0]).toMatchObject({ id: 99 });
  });
});
