/**
 * Spec 09B §10 — o arquiteto no orçamento: casos 04, 05, 06, 07 (lado do
 * orçamento), 08, 09 e 11, mais o painel de custos (D9) e a leitura fora do
 * rascunho (D8). Os casos 01-03 e 07 (lado do cadastro) estão em
 * `products/suppliers/__tests__/arquiteto.spec.ts`; o 10, no
 * `marcenariaForm.spec.ts`.
 *
 * O bloco é montado com a fila, o salvamento automático e as ações DE
 * VERDADE; só a API é simulada (respostas reais do cenário B em `fixtures/`).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { useQuery, VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { computed, defineComponent, h, ref } from 'vue';

// --- API simulada ----------------------------------------------------------------
const putRt = vi.fn();                                     // PUT /orcamentos/{id}/rt
const patch = vi.fn();                                     // PATCH do cabeçalho
vi.mock('../services/orcamento.service', async (original) => ({
  ...(await original<typeof import('../services/orcamento.service')>()),
  putRt: (...args: unknown[]) => putRt(...args),
  patchOrcamento: (...args: unknown[]) => patch(...args),
  // A rota própria do select (só id, nome e escritório).
  getArquitetos: async () => [
    { id: 1, nome: 'Studio Renascer', nome_fantasia: null },
    { id: 2, nome: 'Ana Projetos', nome_fantasia: 'Ana Arquitetura' },
  ],
}));
// Quem está logado: o dono (master) ou um vendedor sem permissão de fornecedores.
const usuario = ref<Record<string, unknown>>({ is_master: true, funcionario_id: 1 });
vi.mock('@/shared/stores/auth.store', () => ({ useAuthStore: () => ({ userData: usuario }) }));

const { default: BlocoArquiteto } = await import('../components/editor/BlocoArquiteto.vue');
const { default: PainelCustos } = await import('../components/editor/PainelCustos.vue');
const { default: EditorFaixaStatus } = await import('../components/editor/EditorFaixaStatus.vue');
const { default: EnviarModal } = await import('../components/modais/EnviarModal.vue');
const { default: BaseSelect } = await import('@/shared/components/ui/BaseSelect/BaseSelect.vue');
const { useFornecedorModal } = await import('@/modules/products/suppliers/composables/useFornecedorModal');
const { chaveDetalhe } = await import('../constants/orcamento.constants');
const { proverEditor } = await import('../composables/useEditorContexto');
const { useAcoesOrcamento } = await import('../composables/useAcoesOrcamento');
const { useFilaOrcamento } = await import('../composables/useFilaOrcamento');
const { useSalvamentoAutomatico } = await import('../composables/useSalvamentoAutomatico');
const { orcamentoDetalheSchema } = await import('../schemas/orcamentoDetalhe.schema');
const { detalheFixture, novoQueryClient } = await import('./apoio');
const aprovadoComCustos = (await import('./fixtures/detalhe-aprovado-com-custos.json')).default;
const aprovadoSemCustos = (await import('./fixtures/detalhe-aprovado-sem-custos.json')).default;

type Detalhe = ReturnType<typeof detalheFixture>;
const NOMES: Record<number, string> = { 1: 'Studio Renascer', 2: 'Ana Projetos', 9: 'Novo Escritório' };

/**
 * O PUT /rt simulado responde como o backend: a lista de arquitetos vira a
 * enviada (sem `rt_bp`, o mesmo % se era o mesmo arquiteto, senão o padrão 0%).
 */
function responderPutRt(_id: number, revisao: number, lista: { fornecedor_id: number; rt_bp?: number }[]): Detalhe {
  const base = detalheFixture();
  const antes = base.inclui_custos ? base.arquitetos : [];
  return orcamentoDetalheSchema.parse({
    ...base,
    revisao: revisao + 1,
    arquitetos: lista.map((a) => ({
      fornecedor_id: a.fornecedor_id,
      nome: NOMES[a.fornecedor_id],
      rt_bp: a.rt_bp ?? antes.find((x) => 'rt_bp' in x && x.fornecedor_id === a.fornecedor_id)?.rt_bp ?? 0,
      valor_previsto_centavos: 0,
      conta: null,
    })),
  });
}

/**
 * Monta o bloco com o contexto do editor de verdade: o detalhe vem do cache do
 * TanStack (a fila grava nele), a fila, o salvamento e as ações são os reais.
 */
function montarBloco(inicial: Detalhe = detalheFixture()) {
  const queryClient = novoQueryClient();
  queryClient.setQueryData(chaveDetalhe(inicial.id), inicial);
  const Pai = defineComponent({
    setup() {
      const id = ref<number | null>(inicial.id);
      // `staleTime: Infinity`: o teste não busca nada; só lê o cache.
      const { data: detalhe } = useQuery({ queryKey: chaveDetalhe(inicial.id), queryFn: async () => inicial, staleTime: Infinity });
      const fila = useFilaOrcamento(id);
      const salvamento = useSalvamentoAutomatico(detalhe, fila);
      proverEditor({
        id,
        detalhe,
        form: salvamento.form,
        errosPorCampo: salvamento.errosPorCampo,
        editavel: computed(() => detalhe.value?.acoes.editar ?? false),
        incluiCustos: computed(() => detalhe.value?.inclui_custos ?? false),
        acoes: computed(() => detalhe.value!.acoes),
        acoesOrcamento: useAcoesOrcamento(id, fila),
        garantirOrcamento: async () => id.value,
        confirmar: async () => true,
        abrirMovel: () => {},
      });
      return () => h(BlocoArquiteto);
    },
  });
  const wrapper = mount(Pai, { global: { plugins: [[VueQueryPlugin, { queryClient }], createPinia()] as never } });
  return { wrapper, queryClient };
}

/** Escolhe uma opção do select "Quem indicou" (0 = "Nenhum"). */
async function escolher(wrapper: ReturnType<typeof mount>, valor: number) {
  wrapper.findComponent(BaseSelect).vm.$emit('update:modelValue', valor);
  await flushPromises();
}

/** Anda o relógio falso e deixa as promessas terminarem. */
async function andar(ms: number) {
  await vi.advanceTimersByTimeAsync(ms);
  await flushPromises();
}

/** Um detalhe com custos cujo arquiteto está com 0% (o padrão nasce em 0%). */
function comRtZero(): Detalhe {
  const d = detalheFixture();
  if (d.inclui_custos) d.arquitetos[0].rt_bp = 0;
  return d;
}

beforeEach(() => {
  usuario.value = { is_master: true, funcionario_id: 1 };
  putRt.mockReset();
  putRt.mockImplementation(async (...args: Parameters<typeof responderPutRt>) => responderPutRt(...args));
  patch.mockReset();
});
afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('bloco Arquiteto', () => {
  it('lista: "Nenhum" primeiro, depois os arquitetos com o escritório (D4)', async () => {
    const { wrapper } = montarBloco();
    await flushPromises();
    const opcoes = wrapper.findComponent(BaseSelect).props('options') as { value: number; label: string }[];
    expect(opcoes.map((o) => o.label)).toEqual(['Nenhum', 'Studio Renascer', 'Ana Projetos · Ana Arquitetura']);
    expect(wrapper.findComponent(BaseSelect).props('modelValue')).toBe(1);    // o gravado vem escolhido
  });

  it('04 — sem custos: só o select; trocar manda o arquiteto SEM o %', async () => {
    const { wrapper } = montarBloco(detalheFixture(false));
    await flushPromises();
    expect(wrapper.find('[data-testid="rt-percentual"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="rt-previsto"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Modo:');

    await escolher(wrapper, 2);
    expect(putRt).toHaveBeenCalledTimes(1);
    expect(putRt.mock.calls[0][2]).toEqual([{ fornecedor_id: 2 }]);          // nada de rt_bp
  });

  it('05 — com custos: mudar o % vira UM PUT /rt com rt_bp depois de 800 ms (sem PATCH)', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] });
    const { wrapper } = montarBloco();
    await flushPromises();
    const campo = wrapper.find('[data-testid="rt-percentual"]');
    expect((campo.element as HTMLInputElement).value).toBe('8');            // 800 bp
    expect(wrapper.find('[data-testid="rt-previsto"]').text()).toBe('Studio Renascer recebe R$ 739,11');
    expect(wrapper.text()).toContain('Modo: sai da margem — o preço do orçamento não muda.');

    await campo.setValue('6,5');
    await andar(799);
    expect(putRt).not.toHaveBeenCalled();                                   // ainda dentro dos 800 ms
    await andar(10);
    expect(putRt).toHaveBeenCalledTimes(1);
    expect(putRt.mock.calls[0][2]).toEqual([{ fornecedor_id: 1, rt_bp: 650 }]);
    expect(patch).not.toHaveBeenCalled();                                   // o % não vai no PATCH
  });

  it('05 — % fora de 0 a 30: mensagem no campo e nada é salvo', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] });
    const { wrapper } = montarBloco();
    await flushPromises();
    await wrapper.find('[data-testid="rt-percentual"]').setValue('31');
    await andar(1000);
    expect(wrapper.text()).toContain('O RT deve ficar entre 0% e 30%.');
    expect(putRt).not.toHaveBeenCalled();
  });

  it('digitar o % e trocar o arquiteto logo depois: o % vai para o NOVO (não desfaz a troca)', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] });
    // Rede lenta: cada PUT /rt leva 1 s. Quando o % sair (800 ms), a troca
    // ainda está a caminho: o arquiteto tem de ser lido na VEZ da escrita.
    putRt.mockImplementation((...args: Parameters<typeof responderPutRt>) =>
      new Promise((resolver) => setTimeout(() => resolver(responderPutRt(...args)), 1000)));
    const { wrapper } = montarBloco();
    await flushPromises();
    await wrapper.find('[data-testid="rt-percentual"]').setValue('6');
    wrapper.findComponent(BaseSelect).vm.$emit('update:modelValue', 2);     // antes dos 800 ms
    await andar(3000);
    expect(putRt.mock.calls.map((c) => c[2])).toEqual([
      [{ fornecedor_id: 2 }],                                               // a troca, na hora
      [{ fornecedor_id: 2, rt_bp: 600 }],                                   // o %, para o arquiteto de agora
    ]);
  });

  it('06 — "Nenhum": PUT /rt com a lista vazia', async () => {
    const { wrapper } = montarBloco();
    await flushPromises();
    await escolher(wrapper, 0);
    expect(putRt).toHaveBeenCalledTimes(1);
    expect(putRt.mock.calls[0][2]).toEqual([]);
  });

  it('07 — "Cadastrar arquiteto": cadastro já no tipo; o novo vira o escolhido', async () => {
    const { wrapper } = montarBloco();
    await flushPromises();
    await wrapper.find('[data-testid="cadastrar-arquiteto"]').trigger('click');

    const modal = useFornecedorModal();
    expect(modal.isOpen.value).toBe(true);
    expect(modal.selectedTipo.value).toBe('arquiteto');
    expect(modal.isTipoSelectionStep.value).toBe(false);                    // sem o seletor de tipo
    expect(modal.tipoFixo.value).toBe(true);                                // sem "Voltar"

    modal.avisarCriado({ id: 9, nome: 'Novo Escritório', ativo: true, tipo: 'arquiteto' });
    await flushPromises();
    expect(putRt.mock.calls[0][2]).toEqual([{ fornecedor_id: 9 }]);
    modal.closeModal();
  });

  it('07 — sem permissão de fornecedores nem de produtos: sem "Cadastrar arquiteto"', async () => {
    usuario.value = { is_master: false, funcionario_id: 1, cargo: { permissoes: { view_orcamentos_marcenaria: true } } };
    const { wrapper } = montarBloco(detalheFixture(false));
    await flushPromises();
    expect(wrapper.find('[data-testid="cadastrar-arquiteto"]').exists()).toBe(false);
    expect(wrapper.findComponent(BaseSelect).exists()).toBe(true);          // escolher continua possível
  });

  it('08 (D8) — fora do rascunho: só o nome, sem select', async () => {
    const { wrapper } = montarBloco(orcamentoDetalheSchema.parse(structuredClone(aprovadoComCustos)));
    await flushPromises();
    expect(wrapper.findComponent(BaseSelect).exists()).toBe(false);
    expect(wrapper.find('[data-testid="arquiteto-leitura"]').text()).toBe('Studio Renascer');
    expect((wrapper.find('[data-testid="rt-percentual"]').element as HTMLInputElement).disabled).toBe(true);
  });

  it('11 — arquiteto com 0%, com custos: aviso no bloco', async () => {
    const { wrapper } = montarBloco(comRtZero());
    await flushPromises();
    expect(wrapper.find('[data-testid="aviso-rt-zero"]').text()).toBe(
      'Studio Renascer está sem percentual de RT. Informe o % ou defina um padrão em Configurações › Marcenaria.',
    );
  });

  it('11 — com % (ou sem custos): sem o aviso', async () => {
    expect(montarBloco().wrapper.find('[data-testid="aviso-rt-zero"]').exists()).toBe(false);
    expect(montarBloco(detalheFixture(false)).wrapper.find('[data-testid="aviso-rt-zero"]').exists()).toBe(false);
  });
});

describe('11 — modal de envio', () => {
  it('arquiteto com 0%: o aviso entra junto dos avisos do motor', () => {
    mount(EnviarModal, { props: { isOpen: true, detalhe: comRtZero(), enviando: false }, attachTo: document.body });
    expect(document.body.textContent).toContain('Studio Renascer está sem percentual de RT.');
  });

  it('arquiteto com %: sem o aviso', () => {
    mount(EnviarModal, { props: { isOpen: true, detalhe: detalheFixture(), enviando: false }, attachTo: document.body });
    expect(document.body.textContent).not.toContain('sem percentual de RT');
  });
});

describe('painel de custos (D9)', () => {
  function montarPainel(d: Detalhe) {
    const Pai = defineComponent({
      setup() {
        proverEditor({ detalhe: ref(d), form: {}, editavel: computed(() => true), errosPorCampo: ref({}) } as never);
        return () => h(PainelCustos);
      },
    });
    return mount(Pai);
  }

  it('com arquiteto: "RT — nome (%)" e o valor', () => {
    const linha = montarPainel(detalheFixture()).find('[data-testid="linha-rt"]').text();
    expect(linha).toContain('RT — Studio Renascer (8%)');
    expect(linha).toContain('R$ 739,11');
  });

  it('% com 2 casas não é arredondado para 1', () => {
    const d = detalheFixture();
    if (d.inclui_custos) d.arquitetos[0].rt_bp = 825;
    expect(montarPainel(d).find('[data-testid="linha-rt"]').text()).toContain('(8,25%)');
  });

  it('sem arquiteto: "RT — sem arquiteto" e R$ 0,00', () => {
    const d = detalheFixture();
    if (d.inclui_custos) { d.arquitetos = []; d.calculo.rt_total_centavos = 0; }
    const linha = montarPainel(d).find('[data-testid="linha-rt"]').text();
    expect(linha).toContain('RT — sem arquiteto');
    expect(linha).toContain('R$ 0,00');
  });
});

describe('faixa do aprovado (D10)', () => {
  const aprovado = (comCustos = true): Detalhe =>
    orcamentoDetalheSchema.parse(structuredClone(comCustos ? aprovadoComCustos : aprovadoSemCustos));
  /** A conta como a 09A devolve depois de finalizar a OS. */
  function comConta(status = 'PENDENTE'): Detalhe {
    const d = aprovado();
    if (d.inclui_custos) d.arquitetos[0].conta = { id: 3, status, valor_centavos: 42923, vencimento: '2026-12-05' };
    return d;
  }

  it('08 — antes de finalizar a OS (conta null): o previsto', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: aprovado(), temFinanceiro: true } });
    expect(w.find('[data-testid="faixa-rt"]').text()).toBe(
      'RT de Studio Renascer: previsto R$ 429,23 · conta criada na finalização da OS.',
    );
    expect(w.find('[data-testid="ver-contas-pagar"]').exists()).toBe(false);   // ainda não há conta
  });

  it('08 — com a conta pendente: valor, vencimento e situação; o link abre Contas a Pagar', async () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: comConta(), temFinanceiro: true } });
    expect(w.find('[data-testid="faixa-rt"]').text()).toContain(
      'RT de Studio Renascer: conta a pagar de R$ 429,23, vence 05/12/2026 (Pendente).',
    );
    await w.find('[data-testid="ver-contas-pagar"]').trigger('click');
    expect(w.emitted('contasPagar')).toHaveLength(1);
  });

  it('08 — conta paga: "(Paga)"', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: comConta('PAGA') } });
    expect(w.find('[data-testid="faixa-rt"]').text()).toContain('(Paga).');
  });

  it('09 — sem o módulo Financeiro: o texto, sem o link', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: comConta(), temFinanceiro: false } });
    expect(w.find('[data-testid="faixa-rt"]').exists()).toBe(true);
    expect(w.find('[data-testid="ver-contas-pagar"]').exists()).toBe(false);
  });

  it('sem custos: nenhuma linha de RT (o valor é custo)', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: aprovado(false), temFinanceiro: true } });
    expect(w.find('[data-testid="faixa-rt"]').exists()).toBe(false);
  });
});
