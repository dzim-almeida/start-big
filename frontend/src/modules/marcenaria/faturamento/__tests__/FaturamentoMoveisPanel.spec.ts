/**
 * Faturamento dos móveis (docs/marcenaria-faturamento-plano.md, F3) — o painel
 * "Notas fiscais dos móveis" da aba Entrega.
 *
 * A API é SIMULADA: o teste decide o que o GET respondeu.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { describe, expect, it, vi } from 'vitest';

const resposta = { atual: {} as Record<string, unknown> };
const previa = vi.fn();
const emitir = vi.fn();
const previaSimples = vi.fn();
vi.mock('../services/faturamento.service', () => ({
  getFaturamento: () => Promise.resolve(resposta.atual),
  previaDaNota: (...args: unknown[]) => previa(...args),
  emitirNota: (...args: unknown[]) => emitir(...args),
  previaDoSimplesFaturamento: (...args: unknown[]) => previaSimples(...args),
  emitirSimplesFaturamento: vi.fn(),
}));
const emitirInstalacao = vi.fn();
vi.mock('@/modules/fiscal/services/nfse.service', () => ({
  nfseService: { emitirInstalacao: (...args: unknown[]) => emitirInstalacao(...args) },
}));

const { default: FaturamentoMoveisPanel } = await import('../components/FaturamentoMoveisPanel.vue');

const movel = (movel_id: number, nome: string, extra: Record<string, unknown> = {}) => ({
  movel_id, nome, ambiente: 'Cozinha', quantidade: 1, pronto: false, situacao: null,
  pode_faturar: false, documento: null, ...extra,
});

const LIGADO = {
  numero_os: 'OS-2026-000001', faturamento_modo: 'NOTA_NA_ENTREGA', instalacao_modo: 'EMBUTIDA', notas: [],
  moveis: [
    movel(1, 'Balcão', { pronto: true, situacao: 'NO_ESTOQUE', pode_faturar: true }),
    movel(2, 'Aéreo'),
    movel(3, 'Torre', {
      pronto: true, situacao: 'FATURADO',
      documento: { id: 9, numero: 11, serie: 1, status: 'AUTORIZADA', chave_acesso: null, valor_total: 100, data_emissao: null, mensagem: null },
    }),
  ],
};

async function montar(dados: Record<string, unknown>) {
  resposta.atual = dados;
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = mount(FaturamentoMoveisPanel, {
    props: { numeroOs: 'OS-2026-000001' },
    global: { plugins: [[VueQueryPlugin, { queryClient }] as never] },
  });
  await flushPromises();
  return wrapper;
}

describe('FaturamentoMoveisPanel', () => {
  it('desligado: o painel não aparece', async () => {
    const wrapper = await montar({ ...LIGADO, faturamento_modo: 'DESLIGADO' });
    expect(wrapper.find('[data-testid="faturamento-moveis"]').exists()).toBe(false);
  });

  it('só o móvel pronto no estoque pode ser marcado; o faturado mostra a nota', async () => {
    const wrapper = await montar(LIGADO);

    expect(wrapper.find('[data-testid="marcar-1"]').attributes('disabled')).toBeUndefined();
    expect(wrapper.find('[data-testid="marcar-2"]').attributes('disabled')).toBeDefined();
    expect(wrapper.find('[data-testid="marcar-3"]').attributes('disabled')).toBeDefined();
    expect(wrapper.text()).toContain('NF-e 11');
    expect(wrapper.text()).toContain('Em produção');
  });

  it('"Marcar este ambiente" escolhe os prontos e a prévia vai com eles', async () => {
    previa.mockResolvedValue({ itens: [], totais: { valor_total: 0 }, formas_pagamento: [], avisos: [] });
    const wrapper = await montar(LIGADO);

    await wrapper.findAll('button').find((b) => b.text() === 'Marcar este ambiente')!.trigger('click');
    await wrapper.find('[data-testid="previa-nota"]').trigger('click');
    await flushPromises();

    expect(previa).toHaveBeenCalledWith('OS-2026-000001', [1]);
  });
});

describe('FaturamentoMoveisPanel — entrega futura (F4)', () => {
  it('sem simples faturamento: o aviso e o botão; o móvel pronto ainda não pode ser marcado', async () => {
    previaSimples.mockResolvedValue({ itens: [], totais: { valor_total: 0 }, formas_pagamento: [], avisos: [] });
    const wrapper = await montar({
      ...LIGADO,
      faturamento_modo: 'ENTREGA_FUTURA',
      falta_simples_faturamento: true,
      moveis: [movel(1, 'Balcão', { pronto: true, situacao: 'NO_ESTOQUE', pode_faturar: false })],
    });

    expect(wrapper.find('[data-testid="falta-simples-faturamento"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('falta o simples faturamento');
    await wrapper.find('[data-testid="previa-simples"]').trigger('click');
    await flushPromises();
    expect(previaSimples).toHaveBeenCalledWith('OS-2026-000001');
  });
});

describe('FaturamentoMoveisPanel — instalação em NFS-e (G5)', () => {
  it('fora do modo NFSE: sem o bloco da instalação', async () => {
    const wrapper = await montar(LIGADO);
    expect(wrapper.find('[data-testid="nfse-instalacao"]').exists()).toBe(false);
  });

  it('sem nota ainda: o botão emite a NFS-e da instalação da OS', async () => {
    emitirInstalacao.mockResolvedValue({ status: 'AUTORIZADA', mensagem: null });
    const wrapper = await montar({ ...LIGADO, instalacao_modo: 'NFSE', nfse_instalacao: { valor: 750, documento: null } });

    expect(wrapper.text()).toContain('A instalação sai numa NFS-e');
    await wrapper.find('[data-testid="emitir-nfse-instalacao"]').trigger('click');
    await flushPromises();
    expect(emitirInstalacao).toHaveBeenCalledWith('OS-2026-000001', false);
  });

  it('já emitida: mostra a nota e some o botão (uma por OS)', async () => {
    const wrapper = await montar({
      ...LIGADO,
      instalacao_modo: 'NFSE',
      nfse_instalacao: {
        valor: 750,
        documento: { id: 4, status: 'AUTORIZADA', numero: 12, codigo_verificacao: 'AB12', url_consulta: null, mensagem: null },
      },
    });

    expect(wrapper.find('[data-testid="nfse-instalacao"]').text()).toContain('NFS-e 12');
    expect(wrapper.text()).toContain('verificação AB12');
    expect(wrapper.find('[data-testid="emitir-nfse-instalacao"]').exists()).toBe(false);
  });
});
