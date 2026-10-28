/**
 * "Saldo de hoje": conferir, não redigitar.
 *
 * O campo vem com o saldo de AGORA (âncora + movimento), e confirmar sem mexer
 * grava esse mesmo número em todas as contas — é o que renova a data e tira o
 * lembrete mensal. Antes o campo trazia a âncora velha e só gravava o que
 * mudasse, então um saldo que bateu não tinha como ser confirmado.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const mutateAsync = vi.fn().mockResolvedValue(undefined);
const contas = ref([
  // Declarou R$ 500 há um mês; vendeu R$ 150 depois: o sistema diz R$ 650.
  { id: 1, nome: 'Caixa da loja', tipo: 'CAIXA', principal: true, ativo: true, criado_em: '2026-09-01',
    saldo_informado: 50000, saldo_informado_em: '2026-09-27', saldo_atual: 65000 },
  { id: 2, nome: 'Nubank', tipo: 'BANCO', principal: false, ativo: true, criado_em: '2026-09-01',
    saldo_informado: 100000, saldo_informado_em: '2026-09-27', saldo_atual: 91000 },
]);

vi.mock('../../../shared/composables/useFinanceiro', () => ({
  useContasBancariasQuery: () => ({ data: contas, refetch: vi.fn() }),
  useInformarSaldos: () => ({ mutateAsync, isPending: ref(false) }),
}));

const { default: SaldoContasModal } = await import('../SaldoContasModal.vue');

describe('Saldo de hoje', () => {
  it('mostra o saldo de agora, e não o que foi digitado lá atrás', () => {
    const wrapper = mount(SaldoContasModal, { props: { aberto: true }, attachTo: document.body });
    const info = document.body.querySelectorAll('[data-saldo-info]');
    expect(info[0].textContent).toContain('650,00');
    expect(info[1].textContent).toContain('910,00');
    wrapper.unmount();
  });

  it('confirmar sem mexer grava o saldo de agora em TODAS as contas', async () => {
    const wrapper = mount(SaldoContasModal, { props: { aberto: true }, attachTo: document.body });
    const botao = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.includes('Confirmar saldo'))!;
    botao.click();
    await vi.waitFor(() => expect(mutateAsync).toHaveBeenCalled());

    expect(mutateAsync).toHaveBeenCalledWith([
      { id: 1, saldo_informado: 65000 },
      { id: 2, saldo_informado: 91000 },
    ]);
    wrapper.unmount();
  });
});
