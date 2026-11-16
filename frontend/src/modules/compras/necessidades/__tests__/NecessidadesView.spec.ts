/**
 * Necessidades de compra: produto SEM fornecedor no cadastro não pode travar.
 *
 * Antes, a linha ficava com a caixinha desabilitada ("Cadastre um fornecedor
 * no produto") e o item não entrava em pedido nenhum. Agora a linha oferece
 * todos os fornecedores da loja; escolher um marca a linha e o item vai para o
 * rascunho daquele fornecedor (o backend já aceita item sem vínculo).
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { computed, ref } from 'vue';

import type { NecessidadeGrupo, NecessidadeItem } from '../../shared/types/compras.types';

const mutate = vi.fn();

vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('../../shared/composables/useAcessoCompras', () => ({
  useAcessoCompras: () => ({ podeGerenciar: computed(() => true), podeVerCusto: computed(() => true) }),
}));
vi.mock('../../shared/services/compras.service', () => ({ getFornecedoresQueVendem: vi.fn() }));
vi.mock('@tanstack/vue-query', () => ({
  useQuery: () => ({
    data: ref([
      { id: 7, nome: 'Madeireira Centro LTDA', nome_fantasia: 'Madeireira Centro' },
      { id: 9, nome: 'Ferragens Silva', nome_fantasia: null },
    ]),
  }),
}));

function item(extra: Partial<NecessidadeItem>): NecessidadeItem {
  return {
    produto_id: 1, produto_nome: 'Chapa MDF 15mm', codigo_produto: null, unidade_medida: 'UN',
    saldo: 2, minimo: 10, ideal: null, em_pedido: 0, em_rascunho: 0, rascunhos: [],
    fornecedor_id: null, fornecedor_nome: null, embalagem_id: null, unidade_compra: 'UN', fator: 1,
    sugestao: 8, ultimo_preco: null, alternativa: null, opcoes: [], origem: 'MINIMO',
    reservado_os: 0, ordens: [], media_diaria: null, dura_dias: null,
    ...extra,
  };
}

const grupos = ref<NecessidadeGrupo[]>([]);
vi.mock('../../shared/composables/useCompras', () => ({
  useNecessidadesQuery: () => ({ data: grupos, isLoading: ref(false), isError: ref(false) }),
  useGerarPedidos: () => ({ mutate, isPending: ref(false) }),
}));

const { default: NecessidadesView } = await import('../views/NecessidadesView.vue');

describe('Necessidades › produto sem fornecedor no cadastro', () => {
  it('oferece todos os fornecedores e, ao escolher, o item entra no rascunho', async () => {
    grupos.value = [{ fornecedor_id: null, fornecedor_nome: 'Sem fornecedor cadastrado', itens: [item({})] }];
    const wrapper = mount(NecessidadesView);

    const caixa = wrapper.find('input[type="checkbox"].accent-brand-primary.mt-1');
    expect(caixa.attributes('disabled')).toBeDefined(); // ainda sem fornecedor escolhido

    const select = wrapper.find('select[data-escolher-fornecedor]');
    expect(select.findAll('option').map((o) => o.text())).toEqual([
      'Escolha o fornecedor…', 'Madeireira Centro', 'Ferragens Silva',
    ]);

    await select.setValue('7');
    expect((caixa.element as HTMLInputElement).checked).toBe(true);
    expect(caixa.attributes('disabled')).toBeUndefined();

    const gerar = wrapper.findAll('button').find((b) => b.text().includes('Gerar rascunhos'))!;
    await gerar.trigger('click');
    expect(mutate).toHaveBeenCalledWith(
      [{ produto_id: 1, fornecedor_id: 7, quantidade: 8 }],
      expect.anything(),
    );
  });

  it('produto com fornecedor no cadastro continua como era (sem a lista geral)', () => {
    grupos.value = [{
      fornecedor_id: 3, fornecedor_nome: 'Duratex',
      itens: [item({ fornecedor_id: 3, fornecedor_nome: 'Duratex',
        opcoes: [{ fornecedor_id: 3, fornecedor_nome: 'Duratex', unidade_compra: 'UN', fator: 1 } as never] })],
    }];
    const wrapper = mount(NecessidadesView);

    expect(wrapper.find('select[data-escolher-fornecedor]').exists()).toBe(false);
    expect(wrapper.text()).toContain('Duratex');
  });
});
