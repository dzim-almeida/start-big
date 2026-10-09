/**
 * Spec 04B (marcenaria, D1/D4) — a caixa "Sofre perda no orçamento" no
 * cadastro do produto aparece SÓ no segmento com orçamento técnico (caso 20).
 *
 * O formulário do produto, os fornecedores e o store de configurações são
 * SIMULADOS: o teste só decide se o segmento tem a capacidade.
 */
import { shallowMount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const temOrcamentoTecnico = ref(false);    // o segmento declara `orcamento_tecnico`?

vi.mock('../../../composables/useProductForm', () => ({
  // Só os campos que a seção lê; todos vazios.
  useProductForm: () => ({
    nome: ref(''), codigo_produto: ref(''), codigo_barras: ref(''), unidade_medida: ref(''),
    categoria: ref(''), marca: ref(''), fornecedor_id: ref(''), localizacao_estoque: ref(''),
    observacao: ref(''), sofre_perda: ref(false), temOrcamentoTecnico, errors: ref({}),
  }),
}));
vi.mock('../../../../suppliers/composables/useFornecedoresQuery', () => ({
  useFornecedoresQuery: () => ({ fornecedores: ref([]) }),
}));
vi.mock('@/shared/stores/configuracoes.store', () => ({
  useConfiguracoesStore: () => ({ exigirCodigoBarras: ref(false), exigirCategoria: ref(false), unidadeMedidaPadrao: ref('UN') }),
}));

const { default: DadosProdutoSection } = await import('../DadosProdutoSection.vue');

/** Monta a seção (componentes filhos viram "stubs": aqui só importa o que aparece). */
const montar = () => shallowMount(DadosProdutoSection, { props: { submitCount: 0 } });

describe('caixa "Sofre perda no orçamento"', () => {
  it('20 — informática (sem orçamento técnico): a caixa não aparece', () => {
    temOrcamentoTecnico.value = false;
    expect(montar().find('[data-testid="sofre-perda"]').exists()).toBe(false);
  });

  it('marcenaria: a caixa aparece com o texto de ajuda', () => {
    temOrcamentoTecnico.value = true;
    const caixa = montar().find('[data-testid="sofre-perda"]');
    expect(caixa.exists()).toBe(true);
    expect(caixa.text()).toContain('Marque para chapas e fitas de borda');
  });
});
