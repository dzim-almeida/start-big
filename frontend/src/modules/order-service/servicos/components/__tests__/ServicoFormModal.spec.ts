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
    await vi.waitFor(() => expect(document.body.textContent).toContain('NFS-e Nacional'));
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
