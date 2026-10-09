/**
 * Spec 08B §11 — casos 06 a 18: o modal de aprovação, o desfazer com PIN,
 * a faixa do aprovado, a proposta aprovada e a aba "Orçamento" da OS.
 * Os JSON de `fixtures/` são respostas REAIS da API da 08A (cenário B,
 * aprovando só a Torre Quente com a instalação).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

const simular = vi.fn();
const resumo = vi.fn();
vi.mock('../services/aprovacao.service', async (original) => ({
  ...(await original<typeof import('../services/aprovacao.service')>()),
  simularAprovacao: (...args: unknown[]) => simular(...args),
  getResumoPorOs: (...args: unknown[]) => resumo(...args),
}));
vi.mock('@/shared/services/paymentMethods.service', () => ({
  getPaymentMethodsAll: async () => [{ id: 1, nome: 'PIX', ativo: true }, { id: 2, nome: 'Cheque', ativo: false }],
}));

const { default: AprovarModal } = await import('../components/modais/AprovarModal.vue');
const { default: EditorFaixaStatus } = await import('../components/editor/EditorFaixaStatus.vue');
const { default: OSOrcamentoTab } = await import('../components/os/OSOrcamentoTab.vue');
const { default: PainelResumo } = await import('../components/editor/PainelResumo.vue');
const { proverEditor } = await import('../composables/useEditorContexto');
const { useAprovacao } = await import('../composables/useAprovacao');
const { useFilaOrcamento } = await import('../composables/useFilaOrcamento');
const { resumoPorOsSchema, simulacaoAprovacaoSchema } = await import('../schemas/aprovacao.schema');
const { orcamentoDetalheSchema } = await import('../schemas/orcamentoDetalhe.schema');
const { chaveDetalhe } = await import('../constants/orcamento.constants');
const { montarDadosProposta } = await import('../utils/dadosProposta');
const { detalheFixture, erroApi, montarComposable, novoQueryClient } = await import('./apoio');
const aprovadoComCustos = (await import('./fixtures/detalhe-aprovado-com-custos.json')).default;
const aprovadoSemCustos = (await import('./fixtures/detalhe-aprovado-sem-custos.json')).default;
const simulacaoFixture = (await import('./fixtures/aprovacao-simulacao-com-custos.json')).default;
const resumoFixture = (await import('./fixtures/resumo-por-os.json')).default;

type Detalhe = ReturnType<typeof detalheFixture>;
const aprovado = (comCustos = true): Detalhe => orcamentoDetalheSchema.parse(structuredClone(comCustos ? aprovadoComCustos : aprovadoSemCustos));
const plugins = () => [[VueQueryPlugin, { queryClient: novoQueryClient() }] as const, createPinia()];

beforeEach(() => {
  simular.mockReset();
  simular.mockImplementation(async () => simulacaoAprovacaoSchema.parse(structuredClone(simulacaoFixture)));
  resumo.mockReset();
});
afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('respostas reais da 08A', () => {
  it('detalhe aprovado (com e sem custos), simulação e resumo por OS passam no zod', () => {
    const d = aprovado();
    expect(d.status).toBe('APROVADO');
    expect(d.os?.numero_os).toBe('OS-2026-000001');
    expect(d.aprovacao?.calculo?.total_centavos).toBe(536536);
    expect(aprovado(false).inclui_custos).toBe(false);
    expect(simulacaoAprovacaoSchema.parse(simulacaoFixture).margem_liquida_bp).toBe(3660);
    expect(resumoPorOsSchema.parse(resumoFixture).moveis).toHaveLength(1);
  });
});

describe('AprovarModal', () => {
  /** Abre o modal com o detalhe do cenário B (2 móveis + instalação). */
  function abrir(detalhe: Detalhe = detalheFixture()) {
    const aprovar = vi.fn(async () => true);
    mount(AprovarModal, {
      props: { isOpen: true, detalhe, aprovar },
      global: { plugins: plugins() as never, directives: { maska: {} } },
      attachTo: document.body,
    });
    return { aprovar };
  }
  const el = (testid: string) => document.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;
  const botaoAprovar = () => el('confirmar-aprovacao') as HTMLButtonElement;
  async function esperarPrevia() {
    await vi.advanceTimersByTimeAsync(450);
    await flushPromises();
  }

  beforeEach(() => { vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] }); });

  it('06 — desmarcar todos: botão desabilitado e "Escolha pelo menos um móvel."', async () => {
    abrir();
    await esperarPrevia();
    (el('aprovar-movel-1') as HTMLInputElement).click();
    (el('aprovar-movel-2') as HTMLInputElement).click();
    await flushPromises();
    expect(botaoAprovar().disabled).toBe(true);
    expect(el('erro-moveis')?.textContent).toContain('Escolha pelo menos um móvel.');
  });

  it('07 — sem responder o sinal: botão desabilitado', async () => {
    abrir();
    await esperarPrevia();
    expect(el('bloco-sinal')).not.toBeNull();
    expect(botaoAprovar().disabled).toBe(true);
    (el('sinal-nao') as HTMLInputElement).click();
    await flushPromises();
    expect(botaoAprovar().disabled).toBe(false);
    expect(el('sinal-depois')?.textContent).toContain('lance no Adiantamento da OS');
  });

  it('08 — "Sim" sem forma e sem crédito: erro na forma, nada é enviado', async () => {
    const { aprovar } = abrir();
    await esperarPrevia();
    (el('sinal-sim') as HTMLInputElement).click();
    await flushPromises();
    expect(botaoAprovar().disabled).toBe(true);
    expect(document.body.textContent).toContain('Informe a forma de pagamento do sinal.');
    expect(aprovar).not.toHaveBeenCalled();
  });

  it('09 — 3 mudanças em 300 ms: uma simulação só', async () => {
    abrir();
    await esperarPrevia();
    simular.mockClear();
    (el('aprovar-movel-2') as HTMLInputElement).click();
    await vi.advanceTimersByTimeAsync(100);
    (el('aprovar-movel-2') as HTMLInputElement).click();
    await vi.advanceTimersByTimeAsync(100);
    (el('aprovar-movel-1') as HTMLInputElement).click();
    await esperarPrevia();
    expect(simular).toHaveBeenCalledTimes(1);
    expect((simular.mock.calls[0][1] as { movel_ids: number[] }).movel_ids).toEqual([2]);
  });

  it('10 — simulação com 422 no desconto: erro embaixo do campo e botão desabilitado', async () => {
    abrir();
    await esperarPrevia();
    simular.mockRejectedValue(erroApi(422, { codigo: 'CALCULO_INVALIDO', campo: 'desconto', mensagem: 'O desconto não pode passar do total.' }));
    const reais = el('aprovar-desconto-valor') as HTMLInputElement;
    reais.dispatchEvent(new Event('focus'));
    reais.value = '999999';
    reais.dispatchEvent(new Event('input'));
    await esperarPrevia();
    expect(el('aprovar-desconto-erro')?.textContent).toBe('O desconto não pode passar do total.');
    expect(botaoAprovar().disabled).toBe(true);
  });

  it('11 — avisos do D5 em rascunho e vencido; enviado sem aviso', async () => {
    abrir({ ...detalheFixture(), status: 'RASCUNHO' } as Detalhe);
    expect(el('aviso-status')?.textContent).toContain('registrado como enviado e aprovado ao mesmo tempo');
    document.body.innerHTML = '';
    abrir({ ...detalheFixture(), status: 'VENCIDO', datas: { ...detalheFixture().datas, validade: '2026-10-21' } } as Detalhe);
    expect(el('aviso-status')?.textContent).toContain('A validade terminou em 21/10/2026');
    document.body.innerHTML = '';
    abrir({ ...detalheFixture(), status: 'ENVIADO' } as Detalhe);
    expect(el('aviso-status')).toBeNull();
  });

  it('aprovar envia móveis, instalação e o sinal "ainda não"', async () => {
    const { aprovar } = abrir();
    await esperarPrevia();
    (el('aprovar-movel-2') as HTMLInputElement).click();                // só a Torre Quente
    await esperarPrevia();
    (el('sinal-nao') as HTMLInputElement).click();
    await flushPromises();
    botaoAprovar().click();
    await flushPromises();
    expect(aprovar).toHaveBeenCalledWith({ movel_ids: [1], incluir_instalacao: true, sinal: { recebido: false } });
  });
});

describe('useAprovacao.desfazer (D17)', () => {
  function preparar() {
    const id = ref<number | null>(1);
    const { resultado, queryClient } = montarComposable(() => {
      const fila = useFilaOrcamento(id);
      return { fila, aprovacao: useAprovacao(id, fila) };
    });
    queryClient.setQueryData(chaveDetalhe(1), aprovado());
    return resultado;
  }

  it('12 — REQUER_APROVACAO_GERENTE: pede o PIN e reenvia com codigo_gerente', async () => {
    const corpos: unknown[] = [];
    const servico = await import('../services/aprovacao.service');
    const espiao = vi.spyOn(servico, 'desfazerAprovacao').mockImplementation(async (_id, _rev, corpo) => {
      corpos.push(corpo);
      if (!corpo.codigo_gerente) throw erroApi(400, 'REQUER_APROVACAO_GERENTE');
      return detalheFixture();
    });
    const { aprovacao } = preparar();
    const pedirPin = vi.fn(async () => '1234');
    const entrada = { motivo: 'Engano', destino_sinal: 'CREDITO' as const };
    expect(await aprovacao.desfazer(entrada, pedirPin)).not.toBeNull();
    expect(pedirPin).toHaveBeenCalledWith(false);
    expect(corpos).toEqual([entrada, { ...entrada, codigo_gerente: '1234' }]);
    espiao.mockRestore();
  });

  it('13 — PIN cancelado: nada é reenviado; devolve null', async () => {
    const servico = await import('../services/aprovacao.service');
    const espiao = vi.spyOn(servico, 'desfazerAprovacao').mockRejectedValue(erroApi(400, 'REQUER_APROVACAO_GERENTE'));
    const { aprovacao } = preparar();
    expect(await aprovacao.desfazer({ motivo: 'x', destino_sinal: 'CREDITO' }, async () => null)).toBeNull();
    expect(espiao).toHaveBeenCalledTimes(1);
    espiao.mockRestore();
  });
});

describe('faixa do aprovado (D12, D15, D18)', () => {
  it('aprovado: quem aprovou, a OS e os botões', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: aprovado(), aprovadoPor: 'Admin Master', rotuloStatusOs: 'Aberta' } });
    expect(w.text()).toContain('por Admin Master · OS-2026-000001 (Aberta)');
    expect(w.findAll('button').map((b) => b.text())).toEqual(['Abrir OS', 'Proposta aprovada', 'Desfazer aprovação']);
  });

  it('14 — sem poder desfazer: sem o botão, ícone com os motivos', () => {
    const d = aprovado();
    const semDesfazer = { ...d, acoes: { ...d.acoes, desfazer_aprovacao: false } } as Detalhe;
    const w = mount(EditorFaixaStatus, { props: { detalhe: semDesfazer, motivosDesfazer: ['A OS já não está aberta (status: Em Produção).'] } });
    expect(w.find('[data-testid="acao-desfazer"]').exists()).toBe(false);
    expect(w.find('[data-testid="motivos-desfazer"]').attributes('title')).toContain('Em Produção');
  });

  it('15 — OS cancelada: "Nova versão"', () => {
    const d = aprovado();
    const cancelada = { ...d, os: { ...d.os!, status: 'CANCELADA' }, acoes: { ...d.acoes, desfazer_aprovacao: false, nova_versao: true } } as Detalhe;
    const w = mount(EditorFaixaStatus, { props: { detalhe: cancelada } });
    expect(w.text()).toContain('A OS OS-2026-000001 foi cancelada.');
    expect(w.findAll('button').map((b) => b.text())).toEqual(['Nova versão']);
  });
});

describe('16 — proposta aprovada (D25, D26)', () => {
  it('só os aprovados; totais da aprovação; título e a OS', () => {
    const dados = montarDadosProposta(aprovado(), new Date(2026, 9, 9), { modo: 'aprovada' });
    expect(dados.titulo).toBe('PROPOSTA APROVADA');
    expect(dados.aprovacaoTexto).toContain('OS-2026-000001');
    expect(dados.ambientes.flatMap((a) => a.moveis.map((m) => m.nome))).toEqual(['Torre Quente']);
    expect(dados.totalCentavos).toBe(536536);
    expect(dados.ambientes[0].totalCentavos + (dados.instalacaoCentavos ?? 0)).toBe(dados.subtotalCentavos);   // fecha (C6)
    expect(dados.sinalSituacao).toBe('a receber');
  });

  it('a proposta normal do aprovado continua com tudo o que foi proposto, sem faixa', () => {
    const dados = montarDadosProposta(aprovado(), new Date(2026, 9, 9));
    expect(dados.titulo).toBe('PROPOSTA COMERCIAL');
    expect(dados.faixa).toBeNull();
    expect(dados.ambientes[0].moveis).toHaveLength(2);
  });
});

describe('resumo "Proposto × Aprovado" (D14)', () => {
  it('aprovado diferente do proposto: duas colunas', () => {
    const d = aprovado();
    const Pai = defineComponent({
      setup() {
        proverEditor({ detalhe: ref(d) } as never);                       // o painel só lê o detalhe
        return () => h(PainelResumo);
      },
    });
    const w = mount(Pai);
    expect(w.text()).toContain('Proposto');
    expect(w.find('[data-testid="resumo-total"]').text()).toContain('R$ 9.238,89');
    expect(w.find('[data-testid="resumo-total"]').text()).toContain('R$ 5.365,36');
  });
});

describe('aba "Orçamento" da OS', () => {
  function montarAba(totalOs = 536536) {
    return mount(OSOrcamentoTab, { props: { numeroOs: 'OS-2026-000001', totalOsCentavos: totalOs }, global: { plugins: plugins() as never } });
  }

  it('17 — sinal recebido menor que o combinado: aviso e "Preencher adiantamento"', async () => {
    resumo.mockResolvedValue(resumoPorOsSchema.parse(structuredClone(resumoFixture)));
    const w = montarAba();
    await vi.waitFor(() => expect(w.find('[data-testid="aviso-sinal"]').exists()).toBe(true));
    expect(w.text()).toContain('Torre Quente');
    expect(w.text()).toContain('1 móvel não aprovado');
    expect(w.find('[data-testid="aviso-sinal"]').text()).toContain('recebido R$ 0,00');
    await w.find('[data-testid="preencher-adiantamento"]').trigger('click');
    expect(w.emitted('preencherAdiantamento')).toEqual([[214614]]);
    await w.find('[data-testid="abrir-orcamento"]').trigger('click');
    expect(w.emitted('abrirOrcamento')).toEqual([[1]]);
  });

  it('total da OS diferente do aprovado: a linha com os dois (D22)', async () => {
    resumo.mockResolvedValue(resumoPorOsSchema.parse(structuredClone(resumoFixture)));
    const w = montarAba(550000);
    await vi.waitFor(() => expect(w.find('[data-testid="totais-diferentes"]').exists()).toBe(true));
    expect(w.find('[data-testid="totais-diferentes"]').text()).toContain('total atual da OS: R$ 5.500,00');
  });

  it('18 — OS sem orçamento (404): "Esta OS não foi gerada por um orçamento."', async () => {
    resumo.mockRejectedValue(erroApi(404, { codigo: 'NAO_ENCONTRADO', mensagem: 'Esta OS não veio de um orçamento.' }));
    const w = montarAba();
    await vi.waitFor(() => expect(w.find('[data-testid="sem-orcamento"]').exists()).toBe(true));
    expect(w.text()).toContain('Esta OS não foi gerada por um orçamento.');
  });
});
