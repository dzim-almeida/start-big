/**
 * "Notas desta OS" (docs/nfse-melhorias-plano.md, M5).
 *
 * O que não pode errar: nota só sai quando o cliente pede — "Não emitida" é
 * neutra, sem cobrança —, cada lado mostra o seu valor e só aparece o lado
 * que a OS tem.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';

const notas = vi.fn();
vi.mock('../../../services/orderServiceFiscal.service', () => ({ getNotasDaOs: (n: string) => notas(n) }));

const emitirOS = vi.fn().mockResolvedValue(undefined);
vi.mock('@/shared/composables/useEmitirFiscal', () => ({
  useEmitirFiscal: () => ({ pendencias: ref([]), pendenciasModalOpen: ref(false), isVerificando: ref(false), emitirOS }),
}));
vi.mock('@/modules/fiscal/composables/useNfse', () => ({ useNfseConsultarMutation: () => ({ mutate: vi.fn() }) }));

const { default: OSNotasCard } = await import('../OSNotasCard.vue');

const montar = () =>
  mount(OSNotasCard, {
    props: { osNumero: 'OS-2026-000158' },
    attachTo: document.body,
    global: {
      plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]],
      stubs: { NfseEmitirModal: true, NfseDocumentoDrawer: true, FiscalDocumentoDetailsDrawer: true, PendenciasFiscaisModal: true },
    },
  });

const BASE = { numero_os: 'OS-2026-000158', finalizada: true, total_os: 18000 };

afterEach(() => {
  vi.clearAllMocks();
  document.body.innerHTML = '';
});

describe('Notas desta OS', () => {
  it('peça e serviço: dois cartões com o valor de cada um, "Não emitida" neutra e a soma', async () => {
    notas.mockResolvedValue({
      ...BASE,
      pecas: { tem: true, valor: 4500, modulo: true, documento: null },
      servico: { tem: true, valor: 13500, modulo: true, documentos: [] },
    });
    const wrapper = montar();

    await vi.waitFor(() => expect(wrapper.find('[data-os-notas]').exists()).toBe(true));
    expect(wrapper.find('[data-nota-pecas]').text()).toContain('45,00');
    expect(wrapper.find('[data-nota-servico]').text()).toContain('135,00');
    expect(wrapper.text().match(/Não emitida/g)?.length).toBe(2);
    expect(wrapper.find('[data-nota-pecas]').html()).toContain('bg-zinc-100');   // cinza, sem alarme
    expect(wrapper.text()).toContain('Emita só a que o cliente pedir');
    expect(wrapper.text()).toContain('180,00');

    await wrapper.findAll('button').find((b) => b.text().includes('Emitir NF-e das peças'))!.trigger('click');
    expect(emitirOS).toHaveBeenCalledWith('OS-2026-000158', 'nfe');
    wrapper.unmount();
  });

  it('só serviço: só o cartão da NFS-e; emitida aparece com o número e sem botão de emitir', async () => {
    notas.mockResolvedValue({
      ...BASE,
      pecas: { tem: false, valor: 0, modulo: false, documento: null },
      servico: { tem: true, valor: 8000, modulo: true, documentos: [
        { id: 9, status: 'AUTORIZADA', numero: 23, motivo: null, url_pdf: null, valor: 8000, papel: null },
      ] },
    });
    const wrapper = montar();

    await vi.waitFor(() => expect(wrapper.find('[data-nota-servico]').exists()).toBe(true));
    expect(wrapper.find('[data-nota-pecas]').exists()).toBe(false);
    expect(wrapper.text()).toContain('nº 23');
    expect(wrapper.text()).not.toContain('Emitir NFS-e do serviço');
    wrapper.unmount();
  });

  it('empresa sem NF-e: o cartão das peças explica, sem botão que não funciona', async () => {
    notas.mockResolvedValue({
      ...BASE,
      pecas: { tem: true, valor: 5000, modulo: false, documento: null },
      servico: { tem: false, valor: 0, modulo: true, documentos: [] },
    });
    const wrapper = montar();

    await vi.waitFor(() => expect(wrapper.find('[data-nota-pecas]').exists()).toBe(true));
    expect(wrapper.text()).toContain('não emite NF-e por este sistema');
    expect(wrapper.text()).not.toContain('Emitir NF-e das peças');
    wrapper.unmount();
  });
});
