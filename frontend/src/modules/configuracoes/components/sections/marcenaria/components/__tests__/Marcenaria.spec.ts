/**
 * Spec 04B (marcenaria, D8/D9/D12) — a seção Configurações › Marcenaria.
 *
 * A query e a permissão do usuário são SIMULADAS: o teste decide o que a API
 * respondeu (com ou sem custos) e se o usuário pode alterar.
 */
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const dados = ref<Record<string, unknown> | undefined>();     // o que a API "respondeu"
const podeGerirSimulado = ref(false);                         // a permissão de alterar

vi.mock('../../../../../composables/queries/useConfiguracaoMarcenariaQuery', () => ({
  useConfiguracaoMarcenariaQuery: () => ({ data: dados, isPending: ref(false), isError: ref(false), refetch: vi.fn() }),
}));
vi.mock('@/modules/mainLayout/composables/useCheckPermission', () => ({
  useCheckPermission: () => ({ hasPermission: () => podeGerirSimulado.value }),
}));
// Usuário logado sem ser master (o store de verdade buscaria /usuarios/me).
vi.mock('@/shared/stores/auth.store', () => ({
  useAuthStore: () => ({ userData: ref({ is_master: false }) }),
}));

const { default: Marcenaria } = await import('../Marcenaria.vue');

const COMPLETA = {
  inclui_custos: true, markup_padrao_bp: 9000, perda_padrao_bp: 1000, custo_hora_centavos: 0,
  rt_padrao_bp: 0, rt_modo: 'MARGEM', validade_dias: 15, prazo_entrega_dias: 30,
  etapas_producao: ['Corte', 'Borda'], checklist_vistoria: ['Limpeza final do ambiente'],
};
const PUBLICA = {
  inclui_custos: false, validade_dias: 15, prazo_entrega_dias: 30,
  etapas_producao: ['Corte', 'Borda'], checklist_vistoria: ['Limpeza final do ambiente'],
};

describe('Configurações › Marcenaria', () => {
  it('quem pode alterar: bloco de custos editável, aviso do custo/hora zerado (D12)', () => {
    dados.value = COMPLETA;
    podeGerirSimulado.value = true;
    const wrapper = mount(Marcenaria);

    expect(wrapper.find('[data-testid="bloco-custos"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="somente-leitura"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="aviso-custo-hora"]').exists()).toBe(true);
    expect((wrapper.vm as unknown as { podeGerir: boolean }).podeGerir).toBe(true);
  });

  it('19 — sem a permissão de alterar: somente leitura, frase do D9, campos desabilitados', () => {
    dados.value = COMPLETA;
    podeGerirSimulado.value = false;
    const wrapper = mount(Marcenaria);

    expect(wrapper.find('[data-testid="somente-leitura"]').exists()).toBe(true);
    expect(wrapper.findAll('input').every((i) => i.attributes('disabled') !== undefined)).toBe(true);
    // O modal só mostra "Salvar" quando a seção expõe podeGerir = true.
    expect((wrapper.vm as unknown as { podeGerir: boolean }).podeGerir).toBe(false);
  });

  it('sem ver custos (D8): sem o bloco de custos e com a frase no lugar', () => {
    dados.value = PUBLICA;
    podeGerirSimulado.value = false;
    const wrapper = mount(Marcenaria);

    expect(wrapper.find('[data-testid="bloco-custos"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="custos-ocultos"]').text()).toBe('Os custos e margens estão ocultos para o seu perfil.');
  });

  it('mudar um campo deixa a seção "suja"; resetar volta ao que está salvo', async () => {
    dados.value = COMPLETA;
    podeGerirSimulado.value = true;
    const wrapper = mount(Marcenaria);
    const vm = wrapper.vm as unknown as { isDirty: boolean; resetar: () => void; form: { validade_dias: number } };

    expect(vm.isDirty).toBe(false);
    vm.form.validade_dias = 20;
    await wrapper.vm.$nextTick();
    expect(vm.isDirty).toBe(true);
    vm.resetar();
    await wrapper.vm.$nextTick();
    expect(vm.isDirty).toBe(false);
  });
});
