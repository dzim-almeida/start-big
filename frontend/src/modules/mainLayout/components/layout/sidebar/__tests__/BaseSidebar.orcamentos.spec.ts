/**
 * O item "Orçamentos" do menu (Spec 06B D2) saiu na remodelação da marcenaria
 * (item 1): a lista de orçamentos virou a aba "Orçamento" da tela de Serviços.
 * Estes testes garantem que ele não volta.
 *
 * Tudo em volta é SIMULADO: usuário com todas as permissões, todos os módulos.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

const capacidades = ref<string[]>([]);                         // o que o segmento declara
const permitido = ref<(chave?: string) => boolean>(() => true);

vi.mock('@/modules/mainLayout/store/layout.store', () => ({
  useLayoutStore: () => ({ activeTab: ref(''), isMobile: ref(false), isMobileOpen: ref(false), init: vi.fn(), close: vi.fn() }),
}));
vi.mock('@/shared/stores/auth.store', () => ({
  useAuthStore: () => ({ userData: ref({ is_master: true, empresa: { nome_fantasia: 'Loja' } }), isLoading: ref(false) }),
}));
vi.mock('@/modules/mainLayout/composables/useCheckPermission', () => ({
  useCheckPermission: () => ({ hasPermission: (chave?: string) => permitido.value(chave) }),
}));
vi.mock('@/shared/composables/useOrdemServico', () => ({ useOrdemServico: () => ({ usaOrdemServico: ref(true) }) }));
vi.mock('@/shared/stores/modulos.store', () => ({ useModulosStore: () => ({ temModulo: () => true }) }));
vi.mock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
  useCapacidades: () => ({ tem: (c: string) => capacidades.value.includes(c) }),
}));

const { default: BaseSidebar } = await import('../BaseSidebar.vue');

/** Item do menu simplificado: só o rótulo, para comparar a lista. */
const Item = defineComponent({ props: ['label'], setup: (p) => () => h('span', { class: 'item' }, p.label) });
const Vazio = defineComponent({ setup: () => () => h('span') });

function rotulosDoMenu(): string[] {
  const wrapper = mount(BaseSidebar, {
    global: {
      stubs: { SidebarItem: Item, SidebarItemGroup: Item, CompanyCard: Vazio, SidebarSectionSkeleton: Vazio, AppLogo: Vazio },
    },
  });
  return wrapper.findAll('.item').map((item) => item.text());
}

describe('menu "Orçamentos" (saiu do menu lateral: remodelação item 1)', () => {
  it('marcenaria: sem "Orçamentos" no menu (a lista é a aba "Orçamento" de Serviços)', () => {
    capacidades.value = ['imagem_na_entrada', 'garantia_prazo', 'orcamento_tecnico'];
    const rotulos = rotulosDoMenu();
    expect(rotulos.slice(0, 3)).toEqual(['Início', 'Vendas', 'Serviços']);   // o menu de fato montou
    expect(rotulos).not.toContain('Orçamentos');
  });

  it('o menu é o mesmo com ou sem a capacidade de orçamento técnico', () => {
    capacidades.value = ['diagnostico', 'garantia_prazo'];
    const semCapacidade = rotulosDoMenu();
    capacidades.value = ['orcamento_tecnico'];
    expect(rotulosDoMenu()).toEqual(semCapacidade);
  });
});
