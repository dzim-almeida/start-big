/**
 * NFS-e avulsa, sem OS (docs/nfse-fase2-plano.md, G4).
 *
 * O que não pode errar: os valores vão em CENTAVOS (o campo de dinheiro
 * trabalha em reais) e nada é emitido sem conferir antes.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { computed, ref } from 'vue';

const previewAvulsa = vi.fn();
vi.mock('../../../services/nfse.service', () => ({ nfseService: { previewAvulsa: (d: unknown) => previewAvulsa(d) } }));
vi.mock('../../../services/fiscal.service', () => ({
  fiscalService: { buscarServicoNacional: vi.fn(), buscarNbs: vi.fn() },
}));
vi.mock('../../../composables/useNbsSugeridos', () => ({ useNbsSugeridos: () => computed(() => []) }));

const emitir = vi.fn().mockResolvedValue({ status: 'AUTORIZADA' });
vi.mock('../../../composables/useNfse', () => ({
  CODIGO_NOTA_REPETIDA: 'NOTA_DUPLICADA_SUSPEITA',
  codigoDoErro: (e: any) => e?.response?.data?.detail?.codigo,
  useNfseEmitirAvulsaMutation: () => ({ mutateAsync: emitir, isPending: ref(false) }),
}));

const { default: NfseAvulsaModal } = await import('../NfseAvulsaModal.vue');
const { default: MoneyInput } = await import('@/shared/components/ui/BaseMoneyInput/MoneyInput.vue');
const { default: CodigoFiscalBuscaInput } = await import('../../shared/CodigoFiscalBuscaInput.vue');

function botao(texto: string) {
  return [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes(texto)) as HTMLButtonElement | undefined;
}

afterEach(() => {
  vi.clearAllMocks();
  document.body.innerHTML = '';
});

describe('NFS-e avulsa', () => {
  it('confere, mostra a nota e emite com os valores em centavos', async () => {
    previewAvulsa.mockResolvedValue({
      dps: { codigo_tributacao_nacional_iss: '010701', valor_servico: 200, desconto_incondicionado: 20,
        descricao_servico: 'Consultoria', codigo_opcao_simples_nacional: '2', razao_social_tomador: 'Cliente LTDA' },
    });
    const wrapper = mount(NfseAvulsaModal, { props: { isOpen: true }, attachTo: document.body });

    const [codigo, nbs] = wrapper.findAllComponents(CodigoFiscalBuscaInput);
    codigo.vm.$emit('update:modelValue', '010701');
    nbs.vm.$emit('update:modelValue', '115013000');
    const [valor, desconto] = wrapper.findAllComponents(MoneyInput);
    valor.vm.$emit('update:modelValue', 200);
    desconto.vm.$emit('update:modelValue', 20);
    const textarea = document.body.querySelector('textarea') as HTMLTextAreaElement;
    textarea.value = 'Consultoria em informatica';
    textarea.dispatchEvent(new Event('input'));

    await vi.waitFor(() => expect(botao('Conferir')?.disabled).toBe(false));
    expect(botao('Emitir NFS-e')).toBeUndefined();          // sem conferir, não há emitir
    botao('Conferir')!.click();
    await vi.waitFor(() => expect(document.body.querySelector('[data-preview-avulsa]')).not.toBeNull());
    expect(previewAvulsa).toHaveBeenCalledWith(expect.objectContaining({ valor: 20000, desconto: 2000, codigo_nbs: '115013000' }));
    expect(document.body.textContent).toContain('Cliente LTDA');

    botao('Emitir NFS-e')!.click();
    await vi.waitFor(() => expect(emitir).toHaveBeenCalled());
    expect(emitir.mock.calls[0][0]).toMatchObject({ dados: { valor: 20000, desconto: 2000 }, confirmar: false });
    wrapper.unmount();
  });
});
