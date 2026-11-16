/**
 * Remodelação item 2: endereço da obra pelo modal (partes + busca por CEP).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

// A busca de CEP de verdade chama a internet (ViaCEP); aqui ela devolve um endereço fixo.
const dadosCep = ref<Record<string, string> | undefined>(undefined);
vi.mock('@/shared/composables/useCepLookup', () => ({
  useCepQuery: () => ({ data: dadosCep, isLoading: ref(false), isError: ref(false) }),
}));

import EnderecoObraModal from '../components/modais/EnderecoObraModal.vue';
import { camposVazios, montarEnderecoObra } from '../utils/enderecoObra';

afterEach(() => { document.body.innerHTML = ''; dadosCep.value = undefined; });   // o modal vai para o <body>

describe('montarEnderecoObra', () => {
  it('junta tudo na ordem: rua, número - complemento, bairro, cidade/UF, CEP', () => {
    expect(montarEnderecoObra({
      cep: '01310100', logradouro: 'Avenida Paulista', numero: '1000', complemento: 'Sala 2',
      bairro: 'Bela Vista', cidade: 'São Paulo', estado: 'sp',
    })).toBe('Avenida Paulista, 1000 - Sala 2, Bela Vista, São Paulo/SP, CEP 01310-100');
  });

  it('pula o que está em branco (sem vírgula sobrando)', () => {
    expect(montarEnderecoObra({ ...camposVazios(), logradouro: ' Rua A ', cidade: 'Iguatu' })).toBe('Rua A, Iguatu');
  });

  it('CEP incompleto não entra', () => {
    expect(montarEnderecoObra({ ...camposVazios(), logradouro: 'Rua A', cep: '0131' })).toBe('Rua A');
  });

  it('tudo vazio: texto vazio', () => {
    expect(montarEnderecoObra(camposVazios())).toBe('');
  });
});

describe('EnderecoObraModal', () => {
  const abrir = () => mount(EnderecoObraModal, { props: { isOpen: true }, attachTo: document.body });
  const campo = (id: string) => document.querySelector<HTMLInputElement>(`[data-testid="${id}"] input, input[data-testid="${id}"]`)!;
  const digitar = async (id: string, valor: string) => {
    const input = campo(id);
    input.value = valor;
    input.dispatchEvent(new Event('input'));
    await flushPromises();
  };
  const clicar = async (id: string) => {
    document.querySelector<HTMLButtonElement>(`[data-testid="${id}"]`)!.click();
    await flushPromises();
  };

  it('o CEP encontrado preenche rua, bairro, cidade e UF; confirmar devolve o texto montado', async () => {
    const w = abrir();
    dadosCep.value = { logradouro: 'Avenida Paulista', bairro: 'Bela Vista', localidade: 'São Paulo', uf: 'SP' };
    await flushPromises();
    await digitar('obra-numero', '1000');
    await clicar('obra-confirmar');
    expect(w.emitted('confirmar')?.[0]).toEqual(['Avenida Paulista, 1000, Bela Vista, São Paulo/SP']);
  });

  it('sem rua não confirma e avisa', async () => {
    const w = abrir();
    await digitar('obra-cidade', 'Iguatu');
    await clicar('obra-confirmar');
    expect(w.emitted('confirmar')).toBeUndefined();
    expect(document.body.textContent).toContain('Informe a rua (logradouro).');
  });
});
