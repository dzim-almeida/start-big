/**
 * Spec 08B (marcenaria) ⚠️ código compartilhado da OS — casos 01 a 05c.
 *
 * - Abas do modal de OS: "Separação" (10B), "Produção" (12B) e "Orçamento" só com a capacidade
 *   `orcamento_tecnico` e fora da criação; nos outros segmentos, as abas de hoje (01-03).
 * - A aba inicial pedida por quem abre a OS (12B §7.1, casos 13-14 da 12B).
 * - Cadeado nos itens com `origem` e o grupo "Material do orçamento" (04-05b).
 * - A fábrica saiu do modal (05c, FB1).
 *
 * O contexto do modal e as capacidades do segmento são SIMULADOS.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { computed, defineComponent, h, markRaw, ref, shallowRef } from 'vue';

const capacidades = ref<string[]>([]);
vi.mock('@/modules/order-service/shared/segmento/useCapacidades', () => ({
  useCapacidades: () => ({
    temVistoria: computed(() => capacidades.value.includes('vistoria')),
    temDiagnostico: computed(() => capacidades.value.includes('diagnostico')),
    temImagemNaEntrada: computed(() => capacidades.value.includes('imagem_na_entrada')),
    temOrcamentoTecnico: computed(() => capacidades.value.includes('orcamento_tecnico')),
    temAprovacaoItens: computed(() => false),
    temGarantiaItens: computed(() => false),
  }),
}));
vi.mock('@/modules/order-service/shared/segmento/useObjetoLabels', () => ({
  useObjetoLabels: () => ({ labelSingular: ref('Equipamento'), objetoIcon: shallowRef(markRaw({ render: () => null })) }),
}));
vi.mock('@/modules/order-service/shared/segmento/useTiposDeTrabalho', () => ({ useTiposDeTrabalho: () => ({ temTipos: ref(false) }) }));
vi.mock('@/modules/compras/shared/composables/useAcessoCompras', () => ({ useAcessoCompras: () => ({ podeVer: ref(false) }) }));
vi.mock('@/shared/stores/auth.store', () => ({ useAuthStore: () => ({ userData: ref({ is_master: false }) }) }));
vi.mock('vue-router', async (original) => ({
  ...(await original<typeof import('vue-router')>()),
  useRouter: () => ({ push: vi.fn() }),                    // "Abrir orçamento" não navega no teste
}));

// A aba Produção de verdade busca dados: aqui ela é só um marcador.
vi.mock('@/modules/marcenaria/producao/components/OSProducaoTab.vue', () => ({
  __esModule: true,
  default: defineComponent({ render: () => h('div', { 'data-testid': 'aba-producao-marcador' }) }),
}));

const { default: OSFormTabsContent } = await import('../OSFormTabsContent.vue');
const { useOSCreateFlow } = await import('../../../composables/useOSCreateFlow');
const { default: OSServicesTab } = await import('../OSServicesTab.vue');
const { OS_FORM_VIEW_CONTEXT_KEY } = await import('../../../context/useOSFormView.context');
const { default: fonteAbas } = await import('../OSFormTabsContent.vue?raw');
const { default: fonteShell } = await import('../OSFormModalShell.vue?raw');

/**
 * O contexto do modal de OS: o que importa para as abas, e um `{ value:
 * undefined }` para todo o resto que o template lê (as abas filhas são stubs).
 */
function contexto(criando: boolean) {
  const base: Record<string, unknown> = {
    isOpen: computed(() => true),
    isCreateMode: computed(() => criando),
    currentOSData: computed(() => (criando ? null : { id: 1, numero_os: 'OS-2026-000001', valor_total: 100 })),
    isStructureLocked: computed(() => false),
    isItemsLocked: computed(() => false),
    displayItems: computed(() => []),
    objetoFormData: computed(() => ({})),
    funcionariosOptions: computed(() => [{ value: '', label: '-- Selecione --' }, { value: '7', label: 'Pedro' }]),
  };
  return new Proxy(base, { get: (alvo, chave: string) => (chave in alvo ? alvo[chave] : { value: undefined }) });
}
const Vazio = defineComponent({ setup: () => () => h('div') });

/** Monta as abas do modal de OS com o contexto simulado. */
function montarAbas(criando: boolean) {
  return mount(OSFormTabsContent, {
    global: {
      provide: { [OS_FORM_VIEW_CONTEXT_KEY as symbol]: contexto(criando) },
      stubs: { OSObjetoTab: Vazio, OSObjetoDinamicoTab: Vazio, OSVistoriaTab: Vazio, OSDiagnosticoTab: Vazio, OSServicesTab: Vazio },
    },
  });
}

/** Rótulos das abas do modal de OS para um segmento. */
function abas(caps: string[], criando = false): string[] {
  capacidades.value = caps;
  return montarAbas(criando).findAll('button').map((b) => b.text());
}

/** O rótulo da aba ativa (a que tem o fundo branco). */
const abaAtiva = (w: ReturnType<typeof montarAbas>) => w.findAll('button').find((b) => b.classes().includes('bg-white'))?.text();

describe('abas do modal de OS', () => {
  it('01 — informática: as abas de hoje', () => {
    expect(abas(['diagnostico', 'garantia_prazo'])).toEqual(['Equipamento', 'Diagnóstico', 'Serviços e Peças']);
  });

  it('01 — oficina e serigrafia: as abas de hoje', () => {
    expect(abas(['diagnostico', 'vistoria', 'revisoes'])).toEqual(['Equipamento', 'Vistoria', 'Diagnóstico', 'Serviços e Peças']);
    expect(abas(['imagem_na_entrada'])).toEqual(['Equipamento', 'Imagens', 'Serviços e Peças']);
  });

  it('02 — marcenaria, OS existente: "Separação" (10B), "Produção" (12B) e "Orçamento" depois de "Serviços e Peças"', () => {
    expect(abas(['imagem_na_entrada', 'garantia_prazo', 'orcamento_tecnico'])).toEqual([
      'Equipamento', 'Imagens', 'Serviços e Peças', 'Separação', 'Produção', 'Orçamento',
    ]);
  });

  it('03 — marcenaria, criando a OS: sem as abas', () => {
    const lista = abas(['imagem_na_entrada', 'orcamento_tecnico'], true);
    expect(lista).not.toContain('Orçamento');
    expect(lista).not.toContain('Separação');
  });

  it('12B/14 — sem aba inicial pedida, abre em "objeto" (como hoje)', () => {
    capacidades.value = ['imagem_na_entrada', 'orcamento_tecnico'];
    const w = montarAbas(false);
    expect(abaAtiva(w)).toBe('Equipamento');
  });

  it('12B/13 — o quadro pede "producao": abre na Produção, e o pedido vale uma vez só', async () => {
    capacidades.value = ['imagem_na_entrada', 'orcamento_tecnico'];
    useOSCreateFlow().abaInicial.value = 'producao';
    const w = montarAbas(false);
    await flushPromises();
    expect(abaAtiva(w)).toBe('Produção');
    expect(w.find('[data-testid="aba-producao-marcador"]').exists()).toBe(true);
    expect(useOSCreateFlow().abaInicial.value).toBeNull();
  });

  it('12B — aba pedida que o segmento não tem (informática): abre em "objeto"', () => {
    capacidades.value = ['diagnostico'];
    useOSCreateFlow().abaInicial.value = 'producao';
    const w = montarAbas(false);
    expect(abaAtiva(w)).toBe('Equipamento');
  });

  it('05c — sem o trilho, a aba e a trava de status da fábrica (FB1)', () => {
    for (const fonte of [fonteAbas, fonteShell]) {
      expect(fonte).not.toContain('TrilhoFabrica');
      expect(fonte).not.toContain('OrcamentoFabricaTab');
      expect(fonte).not.toContain('status-da-etapa');
    }
  });
});

describe('cadeado nos itens que vieram do orçamento', () => {
  const base = { ordem_servico_id: 1, quantidade: 1, valor_unitario: 1000, valor_total: 1000, unidade_medida: 'UN' };
  const montar = (itens: Record<string, unknown>[]) => mount(OSServicesTab, { props: { itens: itens as never } });
  const botoesDaLinha = (w: ReturnType<typeof montar>, nome: string) =>
    w.findAll('.group').find((linha) => linha.text().includes(nome))!.findAll('button').length;

  it('04 — serviço com origem: cadeado, sem editar/remover', () => {
    const w = montar([{ ...base, id: 1, nome: 'Torre Quente', tipo: 'SERVICO', origem: 'ORCAMENTO_MARCENARIA' }]);
    expect(botoesDaLinha(w, 'Torre Quente')).toBe(0);
    expect(w.html()).toContain('Veio do orçamento aprovado');
  });

  it('05 — origem null e item novo sem o campo: botões de hoje', () => {
    const w = montar([
      { ...base, id: 2, nome: 'Item manual', tipo: 'SERVICO', origem: null },
      { quantidade: 1, valor_unitario: 500, unidade_medida: 'UN', nome: 'Item novo', tipo: 'PRODUTO' },
    ]);
    expect(botoesDaLinha(w, 'Item manual')).toBe(2);
    expect(botoesDaLinha(w, 'Item novo')).toBe(2);
  });

  it('05a — item com fabrica_orcamento_id (regra de antes): cadeado', () => {
    const w = montar([{ ...base, id: 3, nome: 'Da fábrica', tipo: 'SERVICO', fabrica_orcamento_id: 7 }]);
    expect(botoesDaLinha(w, 'Da fábrica')).toBe(0);
  });

  it('05b — 3 peças embutidas: fora da lista principal, grupo recolhido', async () => {
    const pecas = ['MDF Branco', 'Fita PVC', 'Corrediça'].map((nome, i) => ({
      ...base, id: 10 + i, nome, tipo: 'PRODUTO', origem: 'ORCAMENTO_MARCENARIA', valor_unitario: 0, valor_total: 0,
    }));
    const w = montar([{ ...base, id: 1, nome: 'Torre Quente', tipo: 'SERVICO', origem: 'ORCAMENTO_MARCENARIA' }, ...pecas]);
    expect(w.findAll('.group')).toHaveLength(1);                         // só o móvel na lista principal
    const grupo = w.find('[data-testid="material-orcamento"]');
    expect(grupo.text()).toContain('Material do orçamento (3 itens)');
    expect(grupo.text()).not.toContain('MDF Branco');                    // recolhido por padrão
    await grupo.find('button').trigger('click');
    expect(grupo.text()).toContain('MDF Branco');
  });

  it('editar/remover avisam o índice ORIGINAL da lista', async () => {
    const w = montar([
      { ...base, id: 11, nome: 'Peça', tipo: 'PRODUTO', origem: 'ORCAMENTO_MARCENARIA' },
      { ...base, id: 12, nome: 'Manual', tipo: 'SERVICO', origem: null },
    ]);
    const linha = w.findAll('.group').find((l) => l.text().includes('Manual'))!;
    await linha.findAll('button')[1].trigger('click');                  // remover
    expect(w.emitted('removeItem')).toEqual([[1]]);
  });
});
