/**
 * Spec 09B §10 ⚠️ código compartilhado (cadastro de fornecedor) — casos 01,
 * 02, 03 e 07 (lado do cadastro), mais a prova de não regressão (§7.3).
 *
 * - O seletor de tipo só ganha "Arquiteto / Designer" com a capacidade
 *   `orcamento_tecnico` (marcenaria); nos outros segmentos, as 3 de sempre.
 * - O schema exige CPF (pessoa física) ou CNPJ (jurídica) do arquiteto, e não
 *   muda as regras dos outros tipos.
 * - `openCreateModalWithCallback('arquiteto', cb)` abre direto no formulário e
 *   entrega o fornecedor criado ao `cb`; o `openCreateModal` de sempre não muda.
 *
 * A API e a capacidade do segmento são SIMULADAS.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { computed, ref } from 'vue';

// O segmento faz orçamento técnico? (marcenaria = sim; informática = não)
const temOrcamentoTecnico = ref(false);
vi.mock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
  useCapacidades: () => ({ temOrcamentoTecnico: computed(() => temOrcamentoTecnico.value) }),
}));
// O POST /fornecedores: devolve o fornecedor "gravado".
const criar = vi.fn();
vi.mock('../services/fornecedor.service', async (original) => ({
  ...(await original<typeof import('../services/fornecedor.service')>()),
  createFornecedor: (...args: unknown[]) => criar(...args),
}));

const { default: SupplierTypeSelector } = await import('../components/SupplierTypeSelector.vue');
const { default: FornecedorFormModal } = await import('../components/FornecedorFormModal.vue');
const { FornecedorFormSchema } = await import('../schemas/fornecedor.schema');
const { useFornecedorModal } = await import('../composables/useFornecedorModal');
const { novoQueryClient } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');

/** Os rótulos das opções do seletor de tipo. */
function rotulosDoSeletor(): string[] {
  const w = mount(SupplierTypeSelector);
  return w.findAll('button').map((b) => b.find('p').text());
}

beforeEach(() => {
  temOrcamentoTecnico.value = false;
  criar.mockReset();
  criar.mockImplementation(async (payload: Record<string, unknown>) => ({ id: 9, ativo: true, ...payload }));
});
// Modais montados no teste: desmontados ANTES de limpar o <body> (senão o Vue
// tenta atualizar um nó que não existe mais).
const montados: ReturnType<typeof mount>[] = [];
afterEach(() => {
  montados.splice(0).forEach((w) => w.unmount());
  useFornecedorModal().closeModal();
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('seletor de tipo de fornecedor (D2)', () => {
  it('01 — informática (sem orçamento técnico): as 3 opções de sempre', () => {
    expect(rotulosDoSeletor()).toEqual(['Fornecedor de Produtos', 'Transportadora', 'Entregador']);
  });

  it('02 — marcenaria: 4 opções; a 4ª é "Arquiteto / Designer"', () => {
    temOrcamentoTecnico.value = true;
    const rotulos = rotulosDoSeletor();
    expect(rotulos).toHaveLength(4);
    expect(rotulos[3]).toBe('Arquiteto / Designer');
  });
});

describe('schema do fornecedor (D3)', () => {
  /** Os campos com erro, para um formulário. */
  const errosEm = (dados: Record<string, unknown>) => {
    const r = FornecedorFormSchema.safeParse({ nome: 'Studio Renascer', ...dados });
    return r.success ? [] : r.error.issues.map((i) => i.path.join('.'));
  };

  it('03 — arquiteto PJ sem CNPJ: erro no CNPJ', () => {
    expect(errosEm({ tipo: 'arquiteto', pessoa: 'PJ', cnpj: '' })).toEqual(['cnpj']);
  });

  it('arquiteto PF: pede o CPF (e não o CNPJ)', () => {
    expect(errosEm({ tipo: 'arquiteto', pessoa: 'PF', cpf: '' })).toEqual(['cpf']);
    expect(errosEm({ tipo: 'arquiteto', pessoa: 'PF', cpf: '529.982.247-25' })).toEqual([]);
    expect(errosEm({ tipo: 'arquiteto', pessoa: 'PJ', cnpj: '11.222.333/0001-81' })).toEqual([]);
  });

  it('os outros tipos seguem a regra de antes', () => {
    expect(errosEm({ tipo: 'produto', cnpj: '' })).toEqual(['cnpj']);
    expect(errosEm({ tipo: 'transportadora', cnpj: '' })).toEqual(['cnpj']);
    expect(errosEm({ tipo: 'entregador', cpf: '' })).toEqual(['cpf']);
    expect(errosEm({ tipo: 'entregador', cpf: '52998224725' })).toEqual([]);
  });
});

describe('cadastro aberto já no tipo arquiteto (D4, D5)', () => {
  function montarModal() {
    const w = mount(FornecedorFormModal, {
      attachTo: document.body,                                // o BaseModal vai para o <body>
      global: {
        plugins: [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never,
        directives: { maska: {} },
      },
    });
    montados.push(w);
    return w;
  }
  const texto = () => document.body.textContent ?? '';
  /** Digita num campo do modal pelo rótulo (o BaseInput liga o <label> ao <input>). */
  async function digitar(rotulo: string, valor: string) {
    const label = [...document.body.querySelectorAll('label')].find((l) => l.textContent?.trim().startsWith(rotulo))!;
    const input = document.getElementById(label.getAttribute('for')!) as HTMLInputElement;
    input.value = valor;
    input.dispatchEvent(new Event('input'));
    await flushPromises();
  }
  const botao = (rotulo: string) =>
    [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === rotulo) as HTMLButtonElement | undefined;

  it('07 — sem o seletor e sem "Voltar"; salvar entrega o novo ao callback', async () => {
    temOrcamentoTecnico.value = true;
    const callback = vi.fn();
    useFornecedorModal().openCreateModalWithCallback('arquiteto', callback);
    montarModal();
    await flushPromises();

    expect(texto()).toContain('Dados do Arquiteto / Designer');
    expect(texto()).not.toContain('Selecione o tipo de fornecedor');
    expect(botao('Voltar')).toBeUndefined();

    await digitar('Nome', 'Studio Renascer');
    await digitar('CNPJ', '11222333000181');
    botao('Cadastrar Fornecedor')!.click();
    await flushPromises();
    await vi.waitFor(() => expect(criar).toHaveBeenCalledTimes(1));      // a validação do vee-validate é assíncrona

    const payload = criar.mock.calls[0][0];
    expect(payload).toMatchObject({ tipo: 'arquiteto', nome: 'Studio Renascer', cnpj: '11222333000181' });
    expect(payload.cpf).toBeUndefined();
    await vi.waitFor(() => expect(callback).toHaveBeenCalledTimes(1));
    expect(callback.mock.calls[0][0]).toMatchObject({ id: 9, nome: 'Studio Renascer' });
  });

  it('arquiteto pessoa física: manda o CPF e nenhum CNPJ', async () => {
    temOrcamentoTecnico.value = true;
    useFornecedorModal().openCreateModalWithCallback('arquiteto', () => {});
    montarModal();
    await flushPromises();
    (document.body.querySelector('[data-testid="pessoa-pf"]') as HTMLInputElement).click();
    await flushPromises();
    await digitar('Nome', 'Ana Projetos');
    await digitar('CPF', '52998224725');
    botao('Cadastrar Fornecedor')!.click();
    await vi.waitFor(() => expect(criar).toHaveBeenCalledTimes(1));
    expect(criar.mock.calls[0][0]).toMatchObject({ tipo: 'arquiteto', cpf: '52998224725' });
    expect(criar.mock.calls[0][0].cnpj).toBeUndefined();
  });

  it('§7.3 — "Novo fornecedor" de sempre começa pelo seletor e não chama callback antigo', async () => {
    const antigo = vi.fn();
    const modal = useFornecedorModal();
    modal.openCreateModalWithCallback('arquiteto', antigo);
    modal.openCreateModal();                                  // a tela de Produtos abre do jeito de sempre
    expect(modal.isTipoSelectionStep.value).toBe(true);
    expect(modal.tipoFixo.value).toBe(false);
    modal.avisarCriado({ id: 1, nome: 'Madeireira', ativo: true });
    expect(antigo).not.toHaveBeenCalled();
  });

  it('fechar sem salvar esquece o callback', () => {
    vi.useFakeTimers();
    const callback = vi.fn();
    const modal = useFornecedorModal();
    modal.openCreateModalWithCallback('arquiteto', callback);
    modal.closeModal();
    vi.advanceTimersByTime(300);                              // a limpeza roda depois da animação
    modal.avisarCriado({ id: 1, nome: 'Outro', ativo: true });
    expect(callback).not.toHaveBeenCalled();
  });
});
