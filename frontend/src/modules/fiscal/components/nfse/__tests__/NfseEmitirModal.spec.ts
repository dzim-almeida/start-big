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
  CODIGO_NOTA_REPETIDA: 'NOTA_DUPLICADA_SUSPEITA',
  codigoDoErro: (e: any) => e?.response?.data?.detail?.codigo,
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
    await vi.waitFor(() => expect(emitir).toHaveBeenCalledWith({ numeroOs: 'OS-2026-000123', confirmar: false }));
    wrapper.unmount();
  });

  it('nota repetida: mostra o aviso da plataforma e só emite com a confirmação', async () => {
    verificarOs.mockResolvedValue({ completo: true, pendencias: [] });
    previewOs.mockResolvedValue({
      numero_os: 'OS-2026-000123',
      dps: { descricao_servico: 'Formatação', valor_servico: 150, codigo_tributacao_nacional_iss: '010701', codigo_opcao_simples_nacional: '2' },
    });
    emitir.mockRejectedValueOnce({
      response: { data: { detail: { codigo: 'NOTA_DUPLICADA_SUSPEITA', mensagem: 'Igual à ref os-9-nfse, autorizada há 3 min.' } } },
    });
    const wrapper = await conferir();
    await vi.waitFor(() => expect(document.body.querySelector('[data-preview-nfse]')).not.toBeNull());

    botao('Emitir NFS-e')!.click();
    await vi.waitFor(() => expect(document.body.querySelector('[data-aviso-repetida]')).not.toBeNull());
    expect(document.body.textContent).toContain('autorizada há 3 min');
    expect(botao('Emitir NFS-e')!.disabled).toBe(true);

    botao('Emitir mesmo assim')!.click();
    await vi.waitFor(() => expect(emitir).toHaveBeenLastCalledWith({ numeroOs: 'OS-2026-000123', confirmar: true }));
    wrapper.unmount();
  });
});

describe('Uma nota por código (G3)', () => {
  it('cada código tem o seu botão; a emitida aparece marcada', async () => {
    const dps = (codigo: string, valor: number) => ({
      descricao_servico: `Serviço ${codigo}`, valor_servico: valor,
      codigo_tributacao_nacional_iss: codigo, codigo_opcao_simples_nacional: '2',
    });
    verificarOs.mockResolvedValue({ completo: true, pendencias: [] });
    previewOs.mockResolvedValue({
      numero_os: 'OS-2026-000123',
      dps: dps('010701', 150),
      notas: [
        { codigo: '010701', dps: dps('010701', 150), ja_emitida: true },
        { codigo: '140101', dps: dps('140101', 50), ja_emitida: false },
      ],
    });
    const wrapper = await conferir();

    await vi.waitFor(() => expect(document.body.querySelector('[data-varias-notas]')).not.toBeNull());
    const texto = document.body.textContent ?? '';
    expect(texto).toContain('01.07.01');
    expect(texto).toContain('14.01.01');
    expect(texto).toContain('Emitida');
    expect(botao('Emitir NFS-e')).toBeUndefined();          // o rodapé some: cada nota tem o seu

    botao('Emitir esta')!.click();
    await vi.waitFor(() => expect(emitir).toHaveBeenCalledWith({ numeroOs: 'OS-2026-000123', confirmar: false, codigo: '140101' }));
    wrapper.unmount();
  });
});
