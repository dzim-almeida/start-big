/**
 * Emitir a NFS-e de uma OS (backend-fastapi/docs/nfse-plano.md, F3).
 *
 * O que não pode errar: o que falta aparece NOMEADO antes do envio (e o botão
 * não libera), e a nota que vai sair é mostrada como o portal escreve.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const verificarOs = vi.fn();
const previewOs = vi.fn();
vi.mock('../../../services/nfse.service', () => ({
  nfseService: { verificarOs: (n: string) => verificarOs(n), previewOs: (n: string) => previewOs(n) },
}));

const emitir = vi.fn().mockResolvedValue({ status: 'AUTORIZADA' });
vi.mock('../../../composables/useNfse', () => ({
  useNfseEmitirMutation: () => ({ mutateAsync: emitir, isPending: ref(false) }),
}));

const { default: NfseEmitirModal } = await import('../NfseEmitirModal.vue');

async function conferir(numero = 'OS-2026-000123') {
  const wrapper = mount(NfseEmitirModal, { props: { isOpen: true }, attachTo: document.body });
  const input = document.body.querySelector('input') as HTMLInputElement;
  input.value = numero;
  input.dispatchEvent(new Event('input'));
  await vi.waitFor(() => expect(botao('Conferir')?.disabled).toBe(false));
  botao('Conferir')!.click();
  return wrapper;
}

function botao(texto: string) {
  return [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes(texto)) as
    | HTMLButtonElement
    | undefined;
}

afterEach(() => {
  vi.clearAllMocks();
  document.body.innerHTML = '';
});

describe('Emitir NFS-e', () => {
  it('pendências aparecem nomeadas e o botão de emitir não libera', async () => {
    verificarOs.mockResolvedValue({
      completo: false,
      pendencias: [{ categoria: 'item', campo: 'codigo_nbs', mensagem: 'Sem NBS (cadastro do serviço › NFS-e Nacional).', referencia_nome: 'Formatação' }],
    });
    const wrapper = await conferir();

    await vi.waitFor(() => expect(document.body.querySelector('[data-pendencias-nfse]')).not.toBeNull());
    expect(document.body.textContent).toContain('Formatação: Sem NBS');
    expect(previewOs).not.toHaveBeenCalled();
    expect(botao('Emitir NFS-e')!.disabled).toBe(true);
    wrapper.unmount();
  });

  it('completo: mostra a nota como o portal escreve e emite a OS conferida', async () => {
    verificarOs.mockResolvedValue({ completo: true, pendencias: [] });
    previewOs.mockResolvedValue({
      numero_os: 'OS-2026-000123',
      dps: {
        descricao_servico: 'Formatação e backup', valor_servico: 150, desconto_incondicionado: 15,
        codigo_tributacao_nacional_iss: '010701', codigo_nbs: '115013000',
        razao_social_tomador: 'Maria Souza', cpf_tomador: '11144477735', codigo_opcao_simples_nacional: '2',
      },
    });
    const wrapper = await conferir();

    await vi.waitFor(() => expect(document.body.querySelector('[data-preview-nfse]')).not.toBeNull());
    const texto = document.body.textContent ?? '';
    expect(texto).toContain('01.07.01');
    expect(texto).toContain('1.1501.30.00');
    expect(texto).toContain('Maria Souza');
    expect(texto).toContain('150,00');

    botao('Emitir NFS-e')!.click();
    await vi.waitFor(() => expect(emitir).toHaveBeenCalledWith('OS-2026-000123'));
    wrapper.unmount();
  });
});
