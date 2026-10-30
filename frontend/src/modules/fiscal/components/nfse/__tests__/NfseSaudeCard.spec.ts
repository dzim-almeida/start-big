/**
 * Cards e "Saúde Fiscal" da aba NFS-e (docs/nfse-melhorias-plano.md, M4):
 * a mesma barra da aba NF-e, e os cards de status filtrando a tabela.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';

const push = vi.fn();
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));

const saude = ref<any>(undefined);
const documentos = ref<any[]>([]);
vi.mock('../../../composables/useNfse', () => ({
  useNfseSaudeQuery: () => ({ data: saude }),
  useNfseDocumentosQuery: () => ({ documentos, isLoading: ref(false), isError: ref(false) }),
  useNfseConsultarMutation: () => ({ mutate: vi.fn(), isPending: ref(false) }),
  useNfseCancelarMutation: () => ({ mutate: vi.fn(), mutateAsync: vi.fn(), isPending: ref(false) }),
  useNfseTentarDeNovoMutation: () => ({ mutateAsync: tentarDeNovo, isPending: ref(false) }),
}));
const tentarDeNovo = vi.fn();

const obterDocumento = vi.fn();
vi.mock('../../../services/nfse.service', () => ({ nfseService: { obterDocumento: (id: number) => obterDocumento(id) } }));

// A gaveta salva DANFSe/XML pelo "Salvar como"; o utilitário puxa o app inteiro.
const salvarDocumentoFiscal = vi.fn();
vi.mock('../../../utils/salvarDocumentoFiscal', () => ({
  ORIGEM_NFSE: { rotuloPdf: 'DANFSe' },
  salvarDocumentoFiscal: (...args: unknown[]) => salvarDocumentoFiscal(...args),
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
    const wrapper = mount(NfseDocumentosTable, {
      props: { statusFiltro: 'PENDENTE' },
      global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
    });
    expect(wrapper.findAll('[data-nfse-linha]').length).toBe(2);

    await wrapper.setProps({ statusFiltro: 'CANCELADA' });
    expect(wrapper.findAll('[data-nfse-linha]').length).toBe(2);

    await wrapper.setProps({ statusFiltro: null });
    expect(wrapper.findAll('[data-nfse-linha]').length).toBe(5);
    wrapper.unmount();
  });
});

describe('Clicar na linha abre o detalhe da NFS-e (pedido do Alan, 29/10)', () => {
  it('mostra o motivo inteiro e o que fazer', async () => {
    documentos.value = [{ id: 7, status: 'NAO_TRANSMITIDA', numero: null, tomador: 'JOSE WELLINGTON', valor_total: 8000,
      numero_os: 'OS-2026-000158', mensagem: 'Empresa não habilitada para emissão de NFSe no am' }];
    obterDocumento.mockResolvedValue({
      id: 7, status: 'NAO_TRANSMITIDA', numero: null, numero_os: 'OS-2026-000158', ambiente: 1,
      tomador: 'JOSE WELLINGTON', tomador_documento: '02961941318', valor_total: 8000,
      motivo: 'Empresa não habilitada para emissão de NFSe no ambiente de produção',
      dica: 'A NFS-e ainda não está ligada na emissora para este ambiente. Peça ao suporte StartBig para ativar.',
      itens: [{ descricao: 'MANUTENÇÃO EM SISTEMA DE TINTAS HP 416', codigo: '140101', valor: 8000, desconto: 0 }],
      tentativas_anteriores: [], data_emissao: '2026-10-29T12:33:00', data_autorizacao: null,
    });
    const wrapper = mount(NfseDocumentosTable, {
      attachTo: document.body,
      global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
    });

    await wrapper.find('[data-nfse-linha]').trigger('click');

    await vi.waitFor(() => expect(document.body.querySelector('[data-motivo]')?.textContent).toContain('ambiente de produção'));
    expect(obterDocumento).toHaveBeenCalledWith(7);
    expect(document.body.querySelector('[data-dica]')?.textContent).toContain('suporte StartBig');
    expect(document.body.textContent).toContain('MANUTENÇÃO EM SISTEMA DE TINTAS HP 416');
    expect(document.body.textContent).toContain('Produção');
    // Recusada não tem arquivo para baixar.
    expect(document.body.querySelector('[data-arquivos]')).toBeNull();
    wrapper.unmount();
  });

  it('autorizada: DANFSe e XML para baixar, como na NF-e (pedido do Alan, 30/10)', async () => {
    documentos.value = [{ id: 8, status: 'AUTORIZADA', numero: 23, tomador: 'MARIA', valor_total: 8000, numero_os: null }];
    const detalhe = {
      id: 8, status: 'AUTORIZADA', numero: 23, numero_os: null, ambiente: 1, chave_acesso: '2305506',
      tomador: 'MARIA', tomador_documento: null, valor_total: 8000, motivo: null, dica: null,
      url_pdf: '/arquivos/danfse.pdf', url_xml: '/arquivos/nfse.xml', xml_local: true, pdf_local: false,
      itens: [], tentativas_anteriores: [], data_emissao: '2026-10-29T12:33:00', data_autorizacao: '2026-10-29T12:33:05',
    };
    obterDocumento.mockResolvedValue(detalhe);
    const wrapper = mount(NfseDocumentosTable, {
      attachTo: document.body,
      global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
    });

    await wrapper.find('[data-nfse-linha]').trigger('click');
    await vi.waitFor(() => expect(document.body.querySelector('[data-arquivos]')).not.toBeNull());
    expect(document.body.querySelector('[data-arquivos]')?.textContent).toContain('XML guardado neste computador');

    (document.body.querySelector('[data-testid="btn-baixar-xml"]') as HTMLButtonElement).click();
    await vi.waitFor(() => expect(salvarDocumentoFiscal).toHaveBeenCalled());
    expect(salvarDocumentoFiscal.mock.calls[0][0]).toMatchObject({ id: 8 });
    expect(salvarDocumentoFiscal.mock.calls[0][1]).toBe('xml');
    wrapper.unmount();
  });

  it('recusada da OS: "Tentar de novo" envia e a gaveta passa para a tentativa nova (30/10)', async () => {
    documentos.value = [{ id: 7, status: 'NAO_TRANSMITIDA', numero: null, tomador: 'JOSE', valor_total: 8000, numero_os: 'OS-2026-000158' }];
    const base = {
      numero: null, numero_os: 'OS-2026-000158', ambiente: 1, tomador: 'JOSE', tomador_documento: null,
      valor_total: 8000, dica: null, itens: [], tentativas_anteriores: [], data_emissao: '2026-10-30T10:00:00', data_autorizacao: null,
    };
    obterDocumento.mockImplementation(async (id: number) =>
      id === 7
        ? { ...base, id: 7, status: 'NAO_TRANSMITIDA', motivo: 'Empresa não habilitada', pode_tentar_de_novo: true }
        : { ...base, id: 9, status: 'AUTORIZADA', numero: 24, motivo: null, pode_tentar_de_novo: false },
    );
    tentarDeNovo.mockResolvedValue({ documento_id: 9, status: 'AUTORIZADA' });
    const wrapper = mount(NfseDocumentosTable, {
      attachTo: document.body,
      global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
    });

    await wrapper.find('[data-nfse-linha]').trigger('click');
    await vi.waitFor(() => expect(document.body.querySelector('[data-testid="btn-tentar-de-novo"]')).not.toBeNull());
    (document.body.querySelector('[data-testid="btn-tentar-de-novo"]') as HTMLButtonElement).click();

    await vi.waitFor(() => expect(obterDocumento).toHaveBeenCalledWith(9));
    expect(tentarDeNovo).toHaveBeenCalledWith({ id: 7, confirmar: false });
    wrapper.unmount();
  });
});
