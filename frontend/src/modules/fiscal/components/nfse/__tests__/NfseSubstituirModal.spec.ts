/**
 * "Substituir NFS-e" (O4 de docs/nfe-cfop-e-notas-da-os-plano.md).
 *
 * O que não pode errar: sem o porquê (15+ caracteres) não envia; vai o
 * motivo escolhido; e a gaveta passa para a nota NOVA.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const mutateAsync = vi.fn();
vi.mock('../../../composables/useNfse', () => ({
  useNfseSubstituirMutation: () => ({ mutateAsync, isPending: ref(false) }),
}));

const { default: NfseSubstituirModal } = await import('../NfseSubstituirModal.vue');

const montar = () =>
  mount(NfseSubstituirModal, {
    props: { documento: { id: 9, numero: 26 } },
    attachTo: document.body,
  });

const botao = () => document.body.querySelector<HTMLButtonElement>('[data-testid="confirmar-substituicao"]')!;
const texto = () => document.body.querySelector<HTMLTextAreaElement>('[data-substituir-nfse] textarea')!;

afterEach(() => {
  vi.clearAllMocks();
  document.body.innerHTML = '';
});

describe('NfseSubstituirModal', () => {
  it('sem o porquê não envia', async () => {
    const wrapper = montar();
    await flushPromises();

    expect(document.body.textContent).toContain('nº 26');
    expect(botao().disabled).toBe(true);
    wrapper.unmount();
  });

  it('com o porquê: envia o motivo e passa para a nota nova', async () => {
    mutateAsync.mockResolvedValue({ documento_id: 31, status: 'AUTORIZADA' });
    const wrapper = montar();
    await flushPromises();

    const campo = texto();
    campo.value = 'Valor do serviço lançado errado na OS';
    campo.dispatchEvent(new Event('input'));
    await flushPromises();
    botao().click();
    await flushPromises();

    expect(mutateAsync).toHaveBeenCalledWith({
      id: 9, motivo: '99', descricao: 'Valor do serviço lançado errado na OS', confirmar: false,
    });
    expect(wrapper.emitted('substituida')![0]).toEqual([31]);
    wrapper.unmount();
  });
});
