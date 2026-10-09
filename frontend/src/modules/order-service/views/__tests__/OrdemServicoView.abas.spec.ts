/**
 * Spec 11B §11 caso 01 e §8 (prova de não regressão ⚠️ PR1): as abas da tela
 * de Serviços por segmento.
 *
 * - informática / serigrafia: exatamente as abas de hoje;
 * - oficina: + "Revisões", no mesmo lugar;
 * - marcenaria: + "Terceirizados", sem botão de criar no topo (D13).
 *
 * As abas em si são trocadas por marcadores: aqui só importa QUAL aparece.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

// --- Segmento simulado: as capacidades que cada teste liga ----------------------------
const temRevisoes = ref(false);
const temOrcamentoTecnico = ref(false);
vi.mock('../../shared/segmento/useCapacidades', () => ({ useCapacidades: () => ({ temRevisoes, temOrcamentoTecnico }) }));
const podeCriarOSManual = ref(true);
vi.mock('../../shared/segmento/useTiposDeTrabalho', () => ({ useTiposDeTrabalho: () => ({ podeCriarOSManual }) }));
vi.mock('@/modules/marcenaria/orcamentos/composables/usePermissoesOrcamento', () => ({
  usePermissoesOrcamento: () => ({ podeGerir: ref(false) }),
}));
vi.mock('../../servicos/composables/useServicoModal', () => ({ useServicoModal: () => ({ openCreateModal: vi.fn() }) }));
vi.mock('../../ordens/composables/useOSCreateFlow', () => ({ useOSCreateFlow: () => ({ openNovaOS: vi.fn() }) }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }));

/**
 * Um marcador no lugar de cada aba (as de verdade buscam dados). O
 * `__esModule` faz o `defineAsyncComponent` usar o `default`, como no import real.
 */
const marcador = (testid: string) => ({
  __esModule: true,
  default: defineComponent({ render: () => h('div', { 'data-testid': testid }) }),
});
vi.mock('../tabs/OrdensServicoTab.vue', () => marcador('aba-ordens'));
vi.mock('../tabs/ServicosTab.vue', () => marcador('aba-servicos'));
vi.mock('../tabs/RevisoesPendentesTab.vue', () => marcador('aba-revisoes'));
vi.mock('@/modules/marcenaria/terceirizados/components/TerceirizadosTab.vue', () => marcador('aba-terceirizados'));

const { default: OrdemServicoView } = await import('../OrdemServicoView.vue');

const montados: ReturnType<typeof mount>[] = [];
function montar() {
  const w = mount(OrdemServicoView);
  montados.push(w);
  return w;
}
/** Os rótulos das abas, na ordem da tela. */
const abas = (w: ReturnType<typeof mount>) => w.findAll('button').map((b) => b.text()).filter((t) => !t.includes('Nov'));

beforeEach(() => {
  temRevisoes.value = false;
  temOrcamentoTecnico.value = false;
  podeCriarOSManual.value = true;
});
afterEach(() => { montados.splice(0).forEach((w) => w.unmount()); });

describe('01 — abas da tela de Serviços por segmento', () => {
  it('informática / serigrafia: as abas de hoje', () => {
    expect(abas(montar())).toEqual(['Ordens de Serviço', 'Cadastro de Serviços']);
  });

  it('oficina: com "Revisões" no mesmo lugar', () => {
    temRevisoes.value = true;
    expect(abas(montar())).toEqual(['Ordens de Serviço', 'Cadastro de Serviços', 'Revisões']);
  });

  it('marcenaria: com "Terceirizados"; título, subtítulo e sem botão de criar (D10, D13)', async () => {
    temOrcamentoTecnico.value = true;
    podeCriarOSManual.value = false;
    const w = montar();
    expect(abas(w)).toEqual(['Ordens de Serviço', 'Cadastro de Serviços', 'Terceirizados']);

    await w.findAll('button').find((b) => b.text() === 'Terceirizados')!.trigger('click');
    await flushPromises();
    expect(w.find('h2').text()).toBe('Terceirizados');
    expect(w.text()).toContain('Móveis pedidos às centrais parceiras e ainda não conferidos.');
    expect(w.find('[data-testid="aba-terceirizados"]').exists()).toBe(true);
    expect(w.text()).not.toContain('Novo Serviço');
  });
});
