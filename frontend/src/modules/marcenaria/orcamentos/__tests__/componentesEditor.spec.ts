/**
 * Spec 06B §11 — casos 23 a 26: faixa de status, envio, desconto/sinal em
 * % ou R$ e a visão do cliente.
 */
import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it } from 'vitest';
import { defineComponent, h, ref } from 'vue';

import CampoPercentualOuValor from '../components/editor/CampoPercentualOuValor.vue';
import EditorFaixaStatus from '../components/editor/EditorFaixaStatus.vue';
import VisaoClienteView from '../components/editor/VisaoClienteView.vue';
import EnviarModal from '../components/modais/EnviarModal.vue';
import type { AjusteOrcamento, OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';
import { montarDadosProposta } from '../utils/dadosProposta';
import { detalheFixture } from './apoio';

afterEach(() => { document.body.innerHTML = ''; });      // os modais vão para o <body> (Teleport)

/** Detalhe num status, com as ações que o backend daria. */
function emStatus(status: OrcamentoDetalhe['status'], acoes: Partial<OrcamentoDetalhe['acoes']>, extra: Partial<OrcamentoDetalhe> = {}) {
  const d = detalheFixture();
  return {
    ...d,
    status,
    acoes: { ...d.acoes, editar: false, enviar: false, excluir: false, ...acoes },
    datas: { ...d.datas, envio: '2026-10-06T13:00:00', validade: '2026-10-21', recusa: '2026-10-12T13:00:00', aprovacao: '2026-10-15T13:00:00' },
    ...extra,
  } as OrcamentoDetalhe;
}

describe('23 — EditorFaixaStatus (§6.3)', () => {
  const botoes = (w: ReturnType<typeof mount>) => w.findAll('button').map((b) => b.text());

  it('rascunho: sem faixa', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: emStatus('RASCUNHO', { editar: true }) } });
    expect(w.find('[data-testid="faixa-status"]').exists()).toBe(false);
  });

  it('enviado: data de envio, validade e as ações que vierem true', () => {
    const w = mount(EditorFaixaStatus, {
      props: { detalhe: emStatus('ENVIADO', { voltar_a_editar: true, recusar: true, nova_versao: true }) },
    });
    expect(w.text()).toContain('Enviado em 06/10/2026. Vale até 21/10/2026');
    expect(botoes(w)).toEqual(['Voltar a editar', 'Recusar', 'Nova versão']);
  });

  it('as ações seguem `acoes`: sem permissão de gerir, nenhum botão', () => {
    const w = mount(EditorFaixaStatus, { props: { detalhe: emStatus('ENVIADO', {}) } });
    expect(botoes(w)).toEqual([]);
  });

  it('vencido, recusado, substituído e aprovado', () => {
    expect(mount(EditorFaixaStatus, { props: { detalhe: emStatus('VENCIDO', { renovar: true, nova_versao: true, recusar: true }) } }).text())
      .toContain('A validade terminou em 21/10/2026.');
    expect(mount(EditorFaixaStatus, { props: { detalhe: emStatus('RECUSADO', { nova_versao: true }, { motivo_recusa: 'Preço.' }) } }).text())
      .toContain('Recusado em 12/10/2026: Preço.');
    const sub = mount(EditorFaixaStatus, { props: { detalhe: emStatus('SUBSTITUIDO', {}), versaoSubstituta: { id: 9, versao: 3 } } });
    expect(sub.text()).toContain('Esta versão foi substituída pela v3.');
    expect(botoes(sub)).toEqual(['Abrir v3']);
    expect(mount(EditorFaixaStatus, { props: { detalhe: emStatus('APROVADO', {}) } }).text()).toContain('Aprovado em 15/10/2026.');
  });
});

describe('24 — EnviarModal', () => {
  it('sem cliente e sem móvel: lista as duas pendências, sem a terceira', () => {
    const d = detalheFixture();
    const incompleto = { ...d, cliente: null, ambientes: d.ambientes.map((a) => ({ ...a, moveis: [] })) } as OrcamentoDetalhe;
    mount(EnviarModal, { props: { isOpen: true, detalhe: incompleto, enviando: false }, attachTo: document.body });
    const lista = document.querySelector('[data-testid="pendencias-envio"]')!;
    expect(lista.textContent).toContain('Escolha o cliente');
    expect(lista.textContent).toContain('Adicione pelo menos um móvel');
    expect(lista.textContent).not.toContain('Dê um nome ao projeto');           // o projeto tem nome
    expect(document.querySelector('[data-testid="confirmar-envio"]')).toBeNull();
  });

  it('completo: confirmação com total e sinal', () => {
    mount(EnviarModal, { props: { isOpen: true, detalhe: detalheFixture(), enviando: false }, attachTo: document.body });
    const texto = document.querySelector('[data-testid="confirmacao-envio"]')!.textContent!;
    expect(texto).toContain('R$ 9.238,89');
    expect(texto).toContain('R$ 3.695,56');
    expect(texto).toContain('15 dias');
  });
});

describe('25 — CampoPercentualOuValor (D18, Revisão 1)', () => {
  /** Pai mínimo com o v-model e os equivalentes que a API devolveria. */
  function montar(inicial: AjusteOrcamento) {
    const ajuste = ref<AjusteOrcamento>(inicial);
    const Pai = defineComponent({
      setup: () => () => h(CampoPercentualOuValor, {
        nome: 'desconto', rotulo: 'Desconto',
        equivalenteCentavos: 48626, equivalenteBp: 526,          // "da resposta da API"
        modelValue: ajuste.value,
        'onUpdate:modelValue': (novo: AjusteOrcamento) => { ajuste.value = novo; },
      }),
    });
    return { wrapper: mount(Pai), ajuste };
  }

  it('digitar R$: modo VALOR; o % mostra o efetivo da API com "≈"', async () => {
    const { wrapper, ajuste } = montar({ modo: 'PERCENTUAL', valor: 500 });
    const reais = wrapper.find('[data-testid="desconto-valor"]');
    await reais.trigger('focus');
    await reais.setValue('486,26');
    expect(ajuste.value).toEqual({ modo: 'VALOR', valor: 48626 });
    expect(wrapper.find('[data-testid="desconto-equivalente"]').text()).toBe('≈ 5,26%');
  });

  it('digitar %: modo PERCENTUAL; o R$ mostra o valor da API com "≈"', async () => {
    const { wrapper, ajuste } = montar({ modo: 'VALOR', valor: 48626 });
    const pct = wrapper.find('[data-testid="desconto-percentual"]');
    await pct.trigger('focus');
    await pct.setValue('5');
    expect(ajuste.value).toEqual({ modo: 'PERCENTUAL', valor: 500 });
    expect(wrapper.find('[data-testid="desconto-equivalente"]').text()).toBe('≈ R$ 486,26');
  });
});

describe('26 — VisaoClienteView', () => {
  it('nenhum custo, insumo ou preço por móvel na tela', () => {
    const d = detalheFixture();                                       // COM custos
    const w = mount(VisaoClienteView, { props: { dados: montarDadosProposta(d, new Date(2026, 9, 9)) } });
    const texto = w.text();
    expect(texto).toContain('Torre Quente');
    expect(texto).toContain('R$ 8.300,15');                           // total do ambiente
    expect(texto).toContain('R$ 9.238,89');
    expect(texto).not.toMatch(/custo|margem|insumo|markup|MDF Branco/i);
    expect(texto).not.toContain('R$ 4.222,75');                       // preço do móvel (T5)
    expect(texto).not.toContain('R$ 4.077,40');
  });
});
