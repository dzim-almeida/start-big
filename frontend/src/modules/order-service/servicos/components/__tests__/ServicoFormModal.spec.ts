/**
 * Modal do serviço com a NFS-e (backend-fastapi/docs/nfse-plano.md, F1).
 *
 * A regra que não pode quebrar: SEM o módulo NFSE o modal fica exatamente como
 * era (sem seção fiscal) e o salvar não manda os campos da NFS-e — senão uma
 * loja só com NF-e apagaria, sem saber, o código nacional e o NBS gravados.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { computed, ref } from 'vue';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';

const recursos: Record<string, boolean> = {};
vi.mock('@/shared/config/planos', () => ({
  recursoDisponivel: (recurso: string) => !!recursos[recurso],
}));

const update = vi.fn();
const create = vi.fn();
vi.mock('@/modules/order-service/servicos/composables/useServicosMutations', () => ({
  useCreateServicoMutation: () => ({ mutate: create, isPending: ref(false) }),
  useUpdateServicoMutation: () => ({ mutate: update, isPending: ref(false) }),
}));

const fiscalPorServico: Record<number, any> = {
  7: { id: 1, servico_id: 7, codigo_servico_lc116: '0107',
       codigo_tributacao_nacional: '010701', codigo_nbs: '115013000', data_atualizacao: '2026-10-28' },
  9: { id: 2, servico_id: 9, codigo_servico_lc116: '1401', aliquota_iss: 250,
       codigo_tributacao_nacional: '140101', codigo_nbs: '120012000', data_atualizacao: '2026-10-28' },
};
vi.mock('@/modules/order-service/servicos/services/servicos.service', () => ({
  getServicoFiscal: vi.fn((id: number) => Promise.resolve(fiscalPorServico[id] ?? null)),
  getServicos: vi.fn().mockResolvedValue({
    items: [{ id: 7, descricao: 'Suporte em informática' }, { id: 9, descricao: 'Manutenção de impressora' }],
    total_items: 2,
  }),
}));

// Padrão fiscal da loja (M2): Configuração da NFS-e.
const configuracao = vi.fn();
vi.mock('@/modules/fiscal/services/nfse.service', () => ({
  nfseService: { obterConfiguracao: () => configuracao() },
}));

vi.mock('@/shared/stores/auth.store', () => ({
  useAuthStore: () => ({ userData: { empresa: { regime_tributario: 'Simples Nacional - MEI' } } }),
}));

vi.mock('@/modules/fiscal/composables/useNbsSugeridos', () => ({
  useNbsSugeridos: () => computed(() => []),
}));

// A rota da NFS-e (M1 do plano de melhoria): o teste escolhe Nacional ou municipal.
const rotaAtual = ref<{ rota: string; cidade: string | null; obrigatorios: Record<string, boolean>; regime: string }>({
  rota: 'NACIONAL', cidade: null, obrigatorios: {}, regime: 'mei',
});
vi.mock('@/modules/fiscal/composables/useNfseRota', () => ({
  useNfseRota: () => ({
    rota: computed(() => rotaAtual.value),
    municipal: computed(() => rotaAtual.value.rota === 'MUNICIPAL'),
    exige: (campo: string) => rotaAtual.value.rota === 'MUNICIPAL' && rotaAtual.value.obrigatorios[campo] === true,
  }),
}));

const { default: ServicoFormModal } = await import('../ServicoFormModal.vue');
const { useServicoModal } = await import('../../composables/useServicoModal');

const montar = () =>
  mount(ServicoFormModal, {
    attachTo: document.body,
    global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
  });

function abrirEdicao() {
  useServicoModal().openEditModal({ id: 7, descricao: 'Suporte em informática', valor: 15000 } as never);
  return montar();
}

async function salvar() {
  const botao = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes('Salvar Alterações'))!;
  botao.click();
  await vi.waitFor(() => expect(update).toHaveBeenCalled());
  return update.mock.calls[update.mock.calls.length - 1][0].data;
}

afterEach(() => {
  rotaAtual.value = { rota: 'NACIONAL', cidade: null, obrigatorios: {}, regime: 'mei' };
  Object.keys(recursos).forEach((k) => delete recursos[k]);
  update.mockClear();
  create.mockClear();
  configuracao.mockReset();
  document.body.innerHTML = '';
});

describe('Modal do serviço e a NFS-e', () => {
  it('sem o módulo NFSE: modal sem seção fiscal, como sempre foi', async () => {
    recursos.nfe = true;
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Salvar Alterações'));

    expect(document.body.textContent).not.toContain('Dados Fiscais');
    expect(document.body.textContent).not.toContain('NFS-e Nacional');
    wrapper.unmount();
  });

  it('sem o módulo NFSE o salvar não manda (e portanto não apaga) os campos da NFS-e', async () => {
    recursos.nfe = true;
    const wrapper = abrirEdicao();

    const dados = await salvar();

    expect(dados.fiscal).toBeDefined();
    expect(dados.fiscal).not.toHaveProperty('codigo_tributacao_nacional');
    expect(dados.fiscal).not.toHaveProperty('codigo_nbs');
    wrapper.unmount();
  });

  it('com o módulo NFSE: mostra a NFS-e Nacional com os códigos formatados e os salva em dígitos', async () => {
    recursos.nfse = true;            // prestador MEI: só NFS-e, sem NF-e
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Código de Tributação Nacional'));
    await vi.waitFor(() => {
      const valores = [...document.body.querySelectorAll('input')].map((i) => i.value);
      expect(valores).toContain('01.07.01');
      expect(valores).toContain('1.1501.30.00');
    });

    const dados = await salvar();

    expect(dados.fiscal).toMatchObject({ codigo_tributacao_nacional: '010701', codigo_nbs: '115013000' });
    wrapper.unmount();
  });
});

describe('Dados fiscais do serviço mostram só o que a nota pede (M1)', () => {
  it('Nacional/MEI: sem CFOP, CST, unidade nem alíquota de ISS; o salvar não manda (nem apaga) esses campos', async () => {
    recursos.nfse = true;
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('padrão nacional'));

    const texto = document.body.textContent ?? '';
    expect(texto).not.toContain('CFOP');
    expect(texto).not.toContain('CST ICMS');
    expect(texto).not.toContain('Unidade Tributável');
    expect(texto).not.toContain('Alíquota ISS');
    expect(texto).not.toContain('Código LC 116 e');      // o aviso antigo apontava o LC 116 e o CNAE

    const dados = await salvar();
    for (const campo of ['cfop_padrao', 'cst_icms', 'csosn', 'unidade_tributavel']) {
      expect(dados.fiscal).not.toHaveProperty(campo);
    }
    wrapper.unmount();
  });

  it('o item da LC 116 acompanha o código nacional', async () => {
    recursos.nfse = true;
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('preenchido pelo código nacional'));
    expect(document.body.textContent).toContain('01.07');
    wrapper.unmount();
  });

  it('rota municipal: mostra o que a cidade exige, marcado como obrigatório', async () => {
    recursos.nfse = true;
    rotaAtual.value = { rota: 'MUNICIPAL', cidade: 'Iguatu/CE', obrigatorios: { codigo_cnae: true }, regime: 'simples' };
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('prefeitura de Iguatu/CE'));
    expect(document.body.textContent).toContain('CNAE (obrigatório)');
    expect(document.body.textContent).toContain('Código tributário municipal');
    wrapper.unmount();
  });

  it('regime normal: aparece a alíquota de ISS', async () => {
    recursos.nfse = true;
    rotaAtual.value = { rota: 'NACIONAL', cidade: null, obrigatorios: {}, regime: 'normal' };
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Alíquota ISS'));
    wrapper.unmount();
  });

  it('"Detalhes" tem um Editar visível que leva à edição', async () => {
    recursos.nfse = true;
    useServicoModal().openViewModal({ id: 7, descricao: 'Suporte em informática', valor: 15000 } as never);
    const wrapper = montar();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Detalhes do Serviço'));

    const editar = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Editar')!;
    editar.click();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Salvar Alterações'));
    wrapper.unmount();
  });
});

describe('Cadastrar uma vez, reaproveitar (M2)', () => {
  async function abrirCriacao() {
    useServicoModal().closeModal();
    await new Promise((r) => setTimeout(r, 320));        // o closeModal limpa o modo depois de 300 ms
    useServicoModal().openCreateModal();
    return montar();
  }

  function preencherDescricao(texto: string) {
    const input = [...document.body.querySelectorAll('input')].find((i) => i.placeholder?.includes('Troca de display')) as HTMLInputElement
      ?? (document.body.querySelector('input') as HTMLInputElement);
    input.value = texto;
    input.dispatchEvent(new Event('input'));
  }

  it('Novo Serviço já mostra os dados fiscais, vem com o padrão da loja e salva o fiscal junto', async () => {
    recursos.nfse = true;
    configuracao.mockResolvedValue({ nfse_padrao_codigo_nacional: '140101', nfse_padrao_nbs: '120012000', nfse_padrao_aliquota_iss: null });
    const wrapper = await abrirCriacao();

    await vi.waitFor(() => {
      const valores = [...document.body.querySelectorAll('input')].map((i) => i.value);
      expect(valores).toContain('14.01.01');
    });
    expect(document.body.textContent).not.toContain('Salve o serviço primeiro');

    preencherDescricao('Manutenção de plotter');
    const botao = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes('Cadastrar Serviço'))!;
    botao.click();
    await vi.waitFor(() => expect(create).toHaveBeenCalled());
    const pedido = create.mock.calls[0][0];
    expect(pedido.fiscal).toMatchObject({ codigo_tributacao_nacional: '140101', codigo_nbs: '120012000', codigo_servico_lc116: '1401' });
    wrapper.unmount();
  });

  it('sem padrão e sem nada preenchido, o cadastro não cria linha fiscal', async () => {
    recursos.nfse = true;
    configuracao.mockResolvedValue({});
    const wrapper = await abrirCriacao();
    await vi.waitFor(() => expect(configuracao).toHaveBeenCalled());

    preencherDescricao('Visita técnica');
    const botao = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes('Cadastrar Serviço'))!;
    botao.click();
    await vi.waitFor(() => expect(create).toHaveBeenCalled());
    expect(create.mock.calls[0][0]).not.toHaveProperty('fiscal');
    wrapper.unmount();
  });

  it('"Copiar de outro serviço" traz os códigos dele (e a alíquota 2,5% não vira 3%)', async () => {
    recursos.nfse = true;
    rotaAtual.value = { rota: 'NACIONAL', cidade: null, obrigatorios: {}, regime: 'normal' };
    const wrapper = abrirEdicao();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Copiar dados fiscais de outro serviço'));

    // A escolha no select (o BaseSelect emite o valor escolhido).
    await vi.waitFor(() => expect(
      wrapper.findAllComponents({ name: 'BaseSelect' }).find((c) => c.props('label') === 'Copiar dados fiscais de outro serviço'),
    ).toBeTruthy());
    const select = wrapper.findAllComponents({ name: 'BaseSelect' }).find((c) => c.props('label') === 'Copiar dados fiscais de outro serviço')!;
    select.vm.$emit('update:modelValue', 9);

    await vi.waitFor(() => {
      const valores = [...document.body.querySelectorAll('input')].map((i) => i.value);
      expect(valores).toContain('14.01.01');
      expect(valores).toContain('2.5');
    });
    wrapper.unmount();
  });
});
