/**
 * Remodelação item 20: aditivos na aba "Orçamento" da OS (lista, total somado
 * e "Novo aditivo"). O serviço e a permissão são SIMULADOS.
 */
import { mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const resumo = vi.fn();
const criar = vi.fn();
vi.mock('../services/aprovacao.service', async (original) => ({
  ...(await original<typeof import('../services/aprovacao.service')>()),
  getResumoPorOs: (...args: unknown[]) => resumo(...args),
  criarAditivo: (...args: unknown[]) => criar(...args),
}));
const podeGerir = ref(true);
vi.mock('../composables/usePermissoesOrcamento', () => ({ usePermissoesOrcamento: () => ({ podeGerir }) }));
const toast = { success: vi.fn(), error: vi.fn() };
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => toast }));

const { default: OSOrcamentoTab } = await import('../components/os/OSOrcamentoTab.vue');
const { resumoPorOsSchema } = await import('../schemas/aprovacao.schema');
const { novoQueryClient } = await import('./apoio');
const resumoFixture = (await import('./fixtures/resumo-por-os.json')).default;

/** O resumo da fixture com os aditivos pedidos (e o total somado como o backend manda). */
function comAditivos(aditivos: Record<string, unknown>[], podeCriar = true) {
  const base = structuredClone(resumoFixture) as Record<string, unknown>;
  const somados = aditivos.filter((a) => a.status === 'APROVADO').reduce((s, a) => s + (a.total_aprovado_centavos as number), 0);
  return resumoPorOsSchema.parse({
    ...base,
    aditivos,
    total_geral_aprovado_centavos: (base.total_aprovado_centavos as number) + somados,
    pode_criar_aditivo: podeCriar,
  });
}
const aditivo = (id: number, status: string, total: number) => ({
  orcamento_id: id, codigo: `ORC-2026-00000${id}`, versao: 1, status, data_aprovacao: null,
  total_aprovado_centavos: status === 'APROVADO' ? total : null, total_centavos: total, motivos_desfazer: [],
  moveis: [{ nome: 'Escrivaninha', ambiente: 'Escritório', quantidade: 1, medidas: { largura_mm: 1200, altura_mm: 750, profundidade_mm: 600 }, os_item_id: null }],
});

function montar(totalOs: number) {
  return mount(OSOrcamentoTab, {
    props: { numeroOs: 'OS-2026-000001', totalOsCentavos: totalOs },
    global: { plugins: [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never },
  });
}

beforeEach(() => { resumo.mockReset(); criar.mockReset(); podeGerir.value = true; toast.error.mockReset(); });

describe('aba "Orçamento" da OS — aditivos (remodelação item 20)', () => {
  it('lista os aditivos e soma no total aprovado só os aprovados', async () => {
    const r = comAditivos([aditivo(2, 'APROVADO', 100000), aditivo(3, 'RASCUNHO', 50000)]);
    resumo.mockResolvedValue(r);
    const w = montar(r.total_geral_aprovado_centavos!);
    await vi.waitFor(() => expect(w.find('[data-testid="aditivo-2"]').exists()).toBe(true));
    expect(w.find('[data-testid="aditivo-3"]').text()).toContain('Rascunho');
    expect(w.find('[data-testid="total-aprovado"]').text()).toContain('6.365,36');   // 5.365,36 + 1.000,00
    expect(w.find('[data-testid="totais-diferentes"]').exists()).toBe(false);        // a OS bate com a soma
    await w.find('[data-testid="abrir-aditivo-3"]').trigger('click');
    expect(w.emitted('abrirOrcamento')).toEqual([[3]]);
  });

  it('"Novo aditivo" cria e abre o editor do aditivo', async () => {
    resumo.mockResolvedValue(comAditivos([]));
    criar.mockResolvedValue({ id: 9 });
    const w = montar(536536);
    await vi.waitFor(() => expect(w.find('[data-testid="novo-aditivo"]').exists()).toBe(true));
    expect(w.find('[data-testid="sem-aditivos"]').exists()).toBe(true);
    await w.find('[data-testid="novo-aditivo"]').trigger('click');
    await vi.waitFor(() => expect(w.emitted('abrirOrcamento')).toEqual([[9]]));
    expect(criar).toHaveBeenCalledWith('OS-2026-000001');
  });

  it('sem "Novo aditivo": OS fechada (o backend diz) ou sem permissão de gerir', async () => {
    resumo.mockResolvedValue(comAditivos([], false));
    const fechada = montar(536536);
    await vi.waitFor(() => expect(fechada.find('[data-testid="aditivos"]').exists()).toBe(true));
    expect(fechada.find('[data-testid="novo-aditivo"]').exists()).toBe(false);

    resumo.mockResolvedValue(comAditivos([], true));
    podeGerir.value = false;
    const semPermissao = montar(536536);
    await vi.waitFor(() => expect(semPermissao.find('[data-testid="aditivos"]').exists()).toBe(true));
    expect(semPermissao.find('[data-testid="novo-aditivo"]').exists()).toBe(false);
  });
});
