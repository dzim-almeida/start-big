/**
 * ⚠️ Código compartilhado da OS — em qual aba o "Adicionar Item" abre.
 *
 * Configurações › Ordens de Serviço › "Adicionar item abre em" (14/11/2026).
 * Padrão Serviço (o de sempre); com Produto, o item novo abre em Produto e o
 * botão de Produto vem primeiro. Editar um item mantém o tipo dele.
 */
import { mount } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { describe, expect, it, vi } from 'vitest';
import { computed, defineComponent, h } from 'vue';

const config = { itemOsAbreEm: 'SERVICO' as 'SERVICO' | 'PRODUTO' };
vi.mock('@/shared/stores/configuracoes.store', () => ({ useConfiguracoesStore: () => config }));
vi.mock('@/modules/order-service/servicos/services/servicos.service', () => ({
  getServicos: vi.fn(), createServico: vi.fn(),
}));
vi.mock('@/modules/products/inventory/composables/useProductsQuery', () => ({
  useProductsQuery: () => ({ data: computed(() => []), isLoading: computed(() => false) }),
}));
vi.mock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
  useCapacidades: () => ({ temAprovacaoItens: computed(() => false), temGarantiaItens: computed(() => false) }),
}));
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
vi.mock('@/shared/components/commons/BaseModal/BaseModal.vue', () => ({
  __esModule: true,
  default: defineComponent({
    props: { isOpen: Boolean, title: String },
    setup(props, { slots }) {
      return () => (props.isOpen ? h('section', [slots.default?.(), slots.footer?.()]) : null);
    },
  }),
}));

const { default: OSItemFormModal } = await import('../OSItemFormModal.vue');

async function abrir(item: Record<string, unknown> | null = null) {
  const w = mount(OSItemFormModal, {
    props: { isOpen: false, item: item as never },
    global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] },
  });
  await w.setProps({ isOpen: true });
  return w;
}
const tipo = (w: Awaited<ReturnType<typeof abrir>>) => (w.vm as unknown as { tipo: string }).tipo;
const toggle = (w: Awaited<ReturnType<typeof abrir>>) => w.get('[data-testid="os-item-toggle-tipo"]');

describe('OSItemFormModal — aba inicial', () => {
  it('padrão: abre em Serviço, na ordem de sempre', async () => {
    config.itemOsAbreEm = 'SERVICO';
    const w = await abrir();
    expect(tipo(w)).toBe('SERVICO');
    expect(toggle(w).classes()).not.toContain('flex-row-reverse');
  });

  it('loja escolheu Produto: abre em Produto e o botão de Produto vem primeiro', async () => {
    config.itemOsAbreEm = 'PRODUTO';
    const w = await abrir();
    expect(tipo(w)).toBe('PRODUTO');
    expect(toggle(w).classes()).toContain('flex-row-reverse');
  });

  it('editar item mantém o tipo do item, qualquer que seja a escolha', async () => {
    config.itemOsAbreEm = 'PRODUTO';
    const w = await abrir({
      tipo: 'SERVICO', nome: 'Alinhamento', unidade_medida: 'UN', quantidade: 1, valor_unitario: 5000,
    });
    expect(tipo(w)).toBe('SERVICO');
  });
});
