/**
 * Spec 11B §11 caso 01 e §8 (prova de não regressão ⚠️ PR1): as abas da tela
 * de Serviços por segmento.
 *
 * - informática / serigrafia: exatamente as abas de hoje;
 * - oficina: + "Revisões", no mesmo lugar;
 * - marcenaria: "Orçamentos" primeiro e sem "Cadastro de Serviços" (12/10/2026), +
 *   "Produção" (12B D15), "Instalações" (13B D15) e "Terceirizados" (11B D10),
 *   sem botão de criar no topo.
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
const podeVerOrcamentos = ref(true);
const podeGerirOrcamentos = ref(false);
vi.mock('@/modules/marcenaria/orcamentos/composables/usePermissoesOrcamento', () => ({
  usePermissoesOrcamento: () => ({ podeVer: podeVerOrcamentos, podeGerir: podeGerirOrcamentos }),
}));
vi.mock('../../servicos/composables/useServicoModal', () => ({ useServicoModal: () => ({ openCreateModal: vi.fn() }) }));
vi.mock('../../ordens/composables/useOSCreateFlow', () => ({ useOSCreateFlow: () => ({ openNovaOS: vi.fn() }) }));
const rota = { query: {} as Record<string, string> };
const replace = vi.fn();
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn(), replace }), useRoute: () => rota }));

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
vi.mock('@/modules/marcenaria/producao/components/QuadroProducaoTab.vue', () => marcador('aba-quadro-producao'));
vi.mock('@/modules/marcenaria/entrega/components/InstalacoesTab.vue', () => marcador('aba-instalacoes'));
vi.mock('@/modules/marcenaria/orcamentos/views/OrcamentosListaView.vue', () => marcador('aba-orcamentos'));

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
  podeVerOrcamentos.value = true;
  podeGerirOrcamentos.value = false;
  rota.query = {};
  replace.mockClear();
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
    expect(abas(w)).toEqual(['Orçamentos', 'Ordens de Serviço', 'Produção', 'Instalações', 'Terceirizados']);

    await w.findAll('button').find((b) => b.text() === 'Terceirizados')!.trigger('click');
    await flushPromises();
    expect(w.find('h2').text()).toBe('Terceirizados');
    expect(w.text()).toContain('Móveis pedidos às centrais parceiras e ainda não conferidos.');
    expect(w.find('[data-testid="aba-terceirizados"]').exists()).toBe(true);
    expect(w.text()).not.toContain('Novo Serviço');
  });

  it('marcenaria: "Instalações" mostra quem instala onde, sem botão de criar (13B D15)', async () => {
    temOrcamentoTecnico.value = true;
    podeCriarOSManual.value = false;
    const w = montar();
    await w.findAll('button').find((b) => b.text() === 'Instalações')!.trigger('click');
    await flushPromises();
    expect(w.find('h2').text()).toBe('Instalações');
    expect(w.find('[data-testid="aba-instalacoes"]').exists()).toBe(true);
    expect(w.text()).not.toContain('Novo Serviço');
  });

  it('marcenaria: "Produção" mostra o quadro da fábrica, sem botão de criar (12B D15)', async () => {
    temOrcamentoTecnico.value = true;
    podeCriarOSManual.value = false;
    const w = montar();
    await w.findAll('button').find((b) => b.text() === 'Produção')!.trigger('click');
    await flushPromises();
    expect(w.find('h2').text()).toBe('Produção');
    expect(w.find('[data-testid="aba-quadro-producao"]').exists()).toBe(true);
    expect(w.text()).not.toContain('Novo Serviço');
  });

  it('informática / serigrafia / oficina: abrem em "Ordens de Serviço", sem aba Orçamentos', () => {
    temRevisoes.value = true;
    const w = montar();
    expect(w.find('[data-testid="aba-ordens"]').exists()).toBe(true);
    expect(w.find('[data-testid="aba-orcamentos"]').exists()).toBe(false);
    expect(w.text()).toContain('Nova OS');
  });

  it('outro segmento com ?aba=orcamentos na URL: ignora e abre em Ordens', () => {
    rota.query = { aba: 'orcamentos' };
    const w = montar();
    expect(w.find('[data-testid="aba-ordens"]').exists()).toBe(true);
    expect(w.find('[data-testid="aba-orcamentos"]').exists()).toBe(false);
  });
});

describe('marcenaria — aba Orçamentos dentro de Serviços (12/10/2026)', () => {
  beforeEach(() => {
    temOrcamentoTecnico.value = true;
    podeCriarOSManual.value = false;
  });

  it('abre na aba Orçamentos, com "Novo orçamento" para quem pode gerir', async () => {
    podeGerirOrcamentos.value = true;
    const w = montar();
    await flushPromises();
    expect(w.find('h2').text()).toBe('Orçamentos');
    expect(w.find('[data-testid="aba-orcamentos"]').exists()).toBe(true);
    expect(w.find('[data-testid="novo-orcamento-os"]').exists()).toBe(true);
    expect(w.text()).not.toContain('Novo Serviço');
  });

  it('volta do editor (?aba=orcamentos) cai na aba Orçamentos; ?aba=ordens, em Ordens', async () => {
    rota.query = { aba: 'ordens' };
    const w = montar();
    expect(w.find('[data-testid="aba-ordens"]').exists()).toBe(true);
  });

  it('?aba=servicos na marcenaria: a aba não existe, abre em Orçamentos', async () => {
    rota.query = { aba: 'servicos' };
    const w = montar();
    await flushPromises();
    expect(w.find('[data-testid="aba-orcamentos"]').exists()).toBe(true);
    expect(w.find('[data-testid="aba-servicos"]').exists()).toBe(false);
  });

  it('sem permissão de ver orçamentos: sem a aba, abre em Ordens', () => {
    podeVerOrcamentos.value = false;
    const w = montar();
    expect(abas(w)).toEqual(['Ordens de Serviço', 'Produção', 'Instalações', 'Terceirizados']);
    expect(w.find('[data-testid="aba-ordens"]').exists()).toBe(true);
  });

  it('trocar de aba grava a aba na URL', async () => {
    const w = montar();
    await w.findAll('button').find((b) => b.text() === 'Produção')!.trigger('click');
    expect(replace).toHaveBeenCalledWith({ query: { aba: 'producao' } });
  });
});
