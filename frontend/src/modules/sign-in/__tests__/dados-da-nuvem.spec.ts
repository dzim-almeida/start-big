/**
 * Setup preenchido com os dados da conta na nuvem (bug do build de teste, 11/2026).
 *
 * O que quebrava:
 * - a busca do CEP roda sozinha ao abrir a etapa "Dados da Loja" e apagava o
 *   número e o complemento que tinham vindo da nuvem;
 * - o e-mail da loja e o do responsável abriam vazios, mesmo com o e-mail da
 *   conta em mãos (a nuvem não guarda um e-mail separado da loja).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';

// O ViaCEP de mentira: responde um endereço para qualquer CEP.
const getAddressByCep = vi.fn();
vi.mock('../services/sign-in.service', () => ({
  getAddressByCep: (...args: unknown[]) => getAddressByCep(...args),
  restaurarBackupDaNuvem: vi.fn(),
  reenviarLink: vi.fn(),
  reconnectLicenca: vi.fn(),
  setupSistema: vi.fn(),
  uploadEmpresaLogo: vi.fn(),
}));

import { useSignIn } from '../composables/useSignIn';
import LojaStep from '../components/steps/LojaStep.vue';

const TITULAR_PF = {
  tipoPessoa: 'PF',
  nomeOuRazao: 'Maria da Silva',
  documento: '123.456.789-09',
  nomeFantasia: null,
  telefone: null,
  celular: '(85) 99999-0000',
  endereco: {
    cep: '60000000',
    logradouro: 'Rua das Flores',
    numero: '123',
    bairro: 'Centro',
    cidade: 'Fortaleza',
    estado: 'CE',
  },
};

/** Monta a etapa da loja com o vue-query que ela usa para buscar o CEP. */
function montarEtapaDaLoja() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return mount(LojaStep, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } });
}

/** Valor do campo cujo valor atual é `valor` (ou undefined se nenhum tiver). */
function campoComValor(tela: ReturnType<typeof mount>, valor: string) {
  return tela.findAll('input').find((c) => (c.element as HTMLInputElement).value === valor);
}

beforeEach(() => {
  useSignIn().resetSignIn(); // o estado do sign-in é único: zera entre testes
  vi.clearAllMocks();
});

describe('dados da nuvem no setup', () => {
  it('endereço e celular do titular vão para os dados da loja', () => {
    const signIn = useSignIn();
    signIn.aplicarTitular(TITULAR_PF);

    expect(signIn.signInData.loja.cep).toBe('60000000');
    expect(signIn.signInData.loja.numero).toBe('123');
    expect(signIn.signInData.loja.celular).toBe('(85) 99999-0000');
  });

  it('o e-mail da conta vira o e-mail da loja e o do responsável', () => {
    const signIn = useSignIn();
    signIn.updateAcessoData({ email: 'dono@exemplo.com.br' }); // o re-login guarda o e-mail
    signIn.aplicarTitular(TITULAR_PF);

    expect(signIn.signInData.loja.emailLoja).toBe('dono@exemplo.com.br');
    expect(signIn.signInData.responsavel.emailResponsavel).toBe('dono@exemplo.com.br');
  });

  it('a busca automática do CEP não apaga o número que veio da nuvem', async () => {
    getAddressByCep.mockResolvedValue({
      logradouro: 'Rua das Flores', bairro: 'Centro', localidade: 'Fortaleza', uf: 'CE', complemento: '',
    });
    useSignIn().aplicarTitular(TITULAR_PF);

    const tela = montarEtapaDaLoja();
    await flushPromises();
    await vi.waitFor(() => expect(getAddressByCep).toHaveBeenCalled()); // a busca rodou...

    await flushPromises();
    expect(campoComValor(tela, '123')).toBeDefined(); // ...e o número continua lá
  });
});
