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

const recursos: Record<string, boolean> = {};
vi.mock('@/shared/config/planos', () => ({
  recursoDisponivel: (recurso: string) => !!recursos[recurso],
}));

const update = vi.fn();
vi.mock('@/modules/order-service/servicos/composables/useServicosMutations', () => ({
  useCreateServicoMutation: () => ({ mutate: vi.fn(), isPending: ref(false) }),
  useUpdateServicoMutation: () => ({ mutate: update, isPending: ref(false) }),
}));

vi.mock('@/modules/order-service/servicos/services/servicos.service', () => ({
  getServicoFiscal: vi.fn().mockResolvedValue({
    id: 1, servico_id: 7, codigo_servico_lc116: '0107',
    codigo_tributacao_nacional: '010701', codigo_nbs: '115013000', data_atualizacao: '2026-10-28',
  }),
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

function abrirEdicao() {
  useServicoModal().openEditModal({ id: 7, descricao: 'Suporte em informática', valor: 15000 } as never);
  return mount(ServicoFormModal, { attachTo: document.body });
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
    const wrapper = mount(ServicoFormModal, { attachTo: document.body });
    await vi.waitFor(() => expect(document.body.textContent).toContain('Detalhes do Serviço'));

    const editar = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Editar')!;
    editar.click();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Salvar Alterações'));
    wrapper.unmount();
  });
});
