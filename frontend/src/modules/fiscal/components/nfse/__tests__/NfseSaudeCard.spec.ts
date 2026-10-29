/**
 * Cards e "Saúde Fiscal" da aba NFS-e (docs/nfse-melhorias-plano.md, M4):
 * a mesma barra da aba NF-e, e os cards de status filtrando a tabela.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const push = vi.fn();
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));

const saude = ref<any>(undefined);
const documentos = ref<any[]>([]);
vi.mock('../../../composables/useNfse', () => ({
  useNfseSaudeQuery: () => ({ data: saude }),
  useNfseDocumentosQuery: () => ({ documentos, isLoading: ref(false), isError: ref(false) }),
  useNfseConsultarMutation: () => ({ mutate: vi.fn(), isPending: ref(false) }),
  useNfseCancelarMutation: () => ({ mutate: vi.fn(), mutateAsync: vi.fn(), isPending: ref(false) }),
}));

const { default: NfseSaudeCard } = await import('../NfseSaudeCard.vue');
const { default: NfseDocumentosTable } = await import('../NfseDocumentosTable.vue');

afterEach(() => {
  saude.value = undefined;
  documentos.value = [];
  vi.clearAllMocks();
  document.body.innerHTML = '';
});

describe('Saúde Fiscal da NFS-e', () => {
  it('mostra a porcentagem e o número de pendências, e o popover diz o que falta', async () => {
    saude.value = {
      percentual: 75,
      pendencias: 1,
      itens: [
        { chave: 'empresa', titulo: 'Dados da empresa', ok: true, detalhe: 'CNPJ e cidade conferem.' },
        {
          chave: 'servicos', titulo: 'Serviços prontos para a nota', ok: false, detalhe: '1 de 2 serviço(s) sem os códigos da NFS-e.',
          servicos: [{ id: 3, nome: 'Montagem', falta: 'código nacional, NBS' }], total_faltando: 1,
        },
      ],
    };
    const wrapper = mount(NfseSaudeCard, { attachTo: document.body });

    expect(wrapper.text()).toContain('75%');
    expect(wrapper.text()).toContain('1');

    await wrapper.find('[data-nfse-saude]').trigger('click');
    expect(document.body.textContent).toContain('Montagem');
    expect(document.body.textContent).toContain('falta código nacional, NBS');

    const abrir = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes('Abrir o cadastro de serviços'))!;
    abrir.click();
    expect(push).toHaveBeenCalledWith('/servicos');
    wrapper.unmount();
  });

  it('sem resposta ainda: 0% e nenhum popover quebrado', async () => {
    const wrapper = mount(NfseSaudeCard, { attachTo: document.body });
    expect(wrapper.text()).toContain('0%');
    await wrapper.find('[data-nfse-saude]').trigger('click');
    expect(document.body.textContent).not.toContain('O que a NFS-e precisa');
    wrapper.unmount();
  });
});

describe('Cards de status filtram a tabela de NFS-e', () => {
  const doc = (id: number, status: string) => ({ id, status, numero: id, tomador: `Cliente ${id}`, valor_total: 1000 });

  it('"Pendentes" inclui as em processamento; "Canceladas" inclui as denegadas', async () => {
    documentos.value = [doc(1, 'AUTORIZADA'), doc(2, 'PROCESSANDO'), doc(3, 'PENDENTE'), doc(4, 'DENEGADA'), doc(5, 'CANCELADA')];
    const wrapper = mount(NfseDocumentosTable, { props: { statusFiltro: 'PENDENTE' } });
    expect(wrapper.findAll('[data-nfse-linha]').length).toBe(2);

    await wrapper.setProps({ statusFiltro: 'CANCELADA' });
    expect(wrapper.findAll('[data-nfse-linha]').length).toBe(2);

    await wrapper.setProps({ statusFiltro: null });
    expect(wrapper.findAll('[data-nfse-linha]').length).toBe(5);
    wrapper.unmount();
  });
});
