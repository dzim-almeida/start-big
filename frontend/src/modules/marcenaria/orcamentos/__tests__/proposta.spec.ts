/**
 * Spec 07 §11 — a proposta comercial: dados (casos 01-09), nome do arquivo
 * (10-11), o documento A4 (12-13) e o fluxo de impressão (14-16).
 * A impressão em si (`window.print`) é SIMULADA.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

const imprimirComPagina = vi.fn();
const toastErro = vi.fn();

vi.mock('@/shared/utils/print.utils', async (original) => ({
  ...(await original<typeof import('@/shared/utils/print.utils')>()),
  imprimirComPagina: (...args: unknown[]) => imprimirComPagina(...args),
  aguardarImagensDaImpressao: async () => undefined,
}));
vi.mock('@/shared/composables/useToast', () => ({
  useToast: () => ({ error: toastErro, success: vi.fn(), warning: vi.fn(), info: vi.fn() }),
}));
// Empresa logada (o cabeçalho da proposta é o mesmo das vias de OS e venda).
vi.mock('@/shared/stores/auth.store', () => ({
  useAuthStore: () => ({ userData: { empresa: { nome_fantasia: 'Marcenaria Exemplo', documento: '12345678000199' } }, enderecoData: null }),
}));

const { default: PropostaPrintTemplate } = await import('../components/print/PropostaPrintTemplate.vue');
const { useImprimirProposta } = await import('../composables/useImprimirProposta');
const { montarDadosProposta } = await import('../utils/dadosProposta');
const { nomeArquivoProposta } = await import('../utils/nomeArquivoProposta');
const { detalheFixture } = await import('./apoio');
type Detalhe = ReturnType<typeof detalheFixture>;

const HOJE = new Date(2026, 9, 9);
const dados = (d: Detalhe = detalheFixture(), versaoSubstituta: number | null = null) =>
  montarDadosProposta(d, HOJE, { versaoSubstituta });
const comStatus = (status: Detalhe['status'], datas: Partial<Detalhe['datas']> = {}) => {
  const d = detalheFixture();
  return { ...d, status, datas: { ...d.datas, ...datas } } as Detalhe;
};

beforeEach(() => {
  imprimirComPagina.mockReset();
  toastErro.mockReset();
});
afterEach(() => { document.body.innerHTML = ''; });

describe('DadosProposta (Spec 07 §6.1)', () => {
  it('01 — com custos na entrada, nenhuma chave de custo/insumo/parâmetro/preço de móvel na saída', () => {
    const chaves = JSON.stringify(dados()).match(/"[a-zA-Z_]+":/g) ?? [];
    for (const chave of chaves) expect(chave).not.toMatch(/custo|margem|insumo|markup|perda|hora|preco|rt_/i);
  });

  it('02 — rascunho: faixa de prévia e validade a partir do envio', () => {
    expect(dados().faixa).toBe('PRÉVIA — proposta ainda não enviada');
    expect(dados().validadeTexto).toBe('15 dias a partir do envio');
  });

  it('03 — enviado com validade 21/10/2026: sem faixa, "até 21/10/2026"', () => {
    const d = dados(comStatus('ENVIADO', { envio: '2026-10-06T13:00:00', validade: '2026-10-21' }));
    expect(d.faixa).toBeNull();
    expect(d.validadeTexto).toBe('até 21/10/2026');
  });

  it('04 — vencido, recusado, substituído (com v3) e aprovado', () => {
    expect(dados(comStatus('VENCIDO', { validade: '2026-10-21' })).faixa).toBe('PROPOSTA VENCIDA em 21/10/2026');
    expect(dados(comStatus('RECUSADO')).faixa).toBe('PROPOSTA RECUSADA');
    expect(dados(comStatus('SUBSTITUIDO'), 3).faixa).toBe('VERSÃO SUBSTITUÍDA pela v3');
    expect(dados(comStatus('APROVADO')).faixa).toBeNull();
  });

  it('05 — ambiente sem móveis fica de fora', () => {
    const d = detalheFixture();
    d.ambientes.push({ ...d.ambientes[0], id: 99, nome: 'Lavabo', moveis: [] } as never);
    expect(dados(d).ambientes.map((a) => a.nome)).toEqual(['Cozinha Gourmet']);
  });

  it('06/07 — desconto percentual mostra "5%"; em valor, só o R$', () => {
    expect(dados().desconto?.percentualTexto).toBe('5%');
    const d = detalheFixture();
    const emValor = { ...d, desconto: { modo: 'VALOR' as const, valor: 48626 } } as Detalhe;
    expect(dados(emValor).desconto).toEqual({ centavos: 48626, percentualTexto: null });
  });

  it('08 — sinal zero: sem sinal (só "Total a pagar")', () => {
    const d = detalheFixture();
    const semSinal = { ...d, calculo: { ...d.calculo, sinal_centavos: 0, saldo_centavos: d.calculo.total_centavos } } as Detalhe;
    expect(dados(semSinal).sinal).toBeNull();
  });

  it('09 — cenário B: ambientes + instalação = subtotal', () => {
    const d = dados();
    expect(d.ambientes.reduce((s, a) => s + a.totalCentavos, 0) + (d.instalacaoCentavos ?? 0)).toBe(d.subtotalCentavos);
  });
});

describe('nome do arquivo (D5)', () => {
  it('10 — caracteres proibidos no Windows viram espaço', () => {
    expect(nomeArquivoProposta({ codigo: 'ORC-2026-000001', versao: 1, cliente: { nome: 'A/B: "Móveis" <SP>' } as never }))
      .toBe('Proposta ORC-2026-000001 v1 - A B Móveis SP');
  });

  it('11 — sem cliente: só o código', () => {
    expect(nomeArquivoProposta({ codigo: 'ORC-2026-000001', versao: 1, cliente: { nome: '' } as never }))
      .toBe('Proposta ORC-2026-000001 v1');
  });

  it('nome de cliente longo é cortado em 40 caracteres', () => {
    const nome = nomeArquivoProposta({ codigo: 'ORC-1', versao: 2, cliente: { nome: 'X'.repeat(80) } as never });
    expect(nome).toBe(`Proposta ORC-1 v2 - ${'X'.repeat(40)}`);
  });
});

describe('documento A4 (§6.2)', () => {
  it('12 — cenário B: textos do desenho e nenhum preço ao lado de móvel', () => {
    mount(PropostaPrintTemplate, { props: { dados: dados() }, attachTo: document.body });
    const doc = document.querySelector('[data-testid="proposta"]')!;
    const texto = doc.textContent!;
    expect(texto).toContain('PROPOSTA COMERCIAL');
    expect(texto).toContain('PRÉVIA — proposta ainda não enviada');
    expect(texto).toContain('Dona Marta');
    expect(texto).toContain('Residencial Alpha Ville - Apto 802');
    expect(texto).toContain('Cozinha Gourmet');                         // (maiúsculas vêm do CSS)
    expect(texto).toContain('R$ 8.300,15');                              // total do ambiente
    expect(texto).toContain('Desconto (5%)');
    expect(document.querySelector('[data-testid="proposta-total"]')!.textContent).toBe('R$ 9.238,89');
    expect(texto).toContain('Sinal na aprovação: R$ 3.695,56 (40%)');
    expect(texto).toContain('Prazo de entrega: 30 dias corridos após a aprovação');
    expect(texto).toContain('Declaro estar de acordo com esta proposta');
    // Nenhum R$ dentro das linhas de móvel (T5).
    for (const movel of document.querySelectorAll('.movel')) expect(movel.textContent).not.toContain('R$');
    expect(texto).not.toContain('R$ 4.222,75');
  });

  it('13 — observações com 3 linhas saem com as quebras', () => {
    const d = detalheFixture();
    mount(PropostaPrintTemplate, {
      props: { dados: dados({ ...d, observacoes_proposta: 'Saldo em 3x\nProjeto 3D aprovado\nEntrega no térreo' } as Detalhe) },
      attachTo: document.body,
    });
    const obs = document.querySelector('[data-testid="proposta-observacoes"]')!;
    expect(obs.textContent!.split('\n')).toHaveLength(3);
    expect(obs.className).toContain('whitespace-pre-line');
  });
});

describe('fluxo de impressão (§6.3)', () => {
  it('14 — algo ficou sem gravar: não imprime e avisa', async () => {
    const { imprimir } = useImprimirProposta({ detalhe: ref(detalheFixture()), gravarPendencias: async () => false });
    expect(await imprimir()).toBe(false);
    expect(imprimirComPagina).not.toHaveBeenCalled();
    expect(toastErro).toHaveBeenCalledWith('A proposta não foi gerada', 'Há alterações que não foram salvas.');
  });

  it('15 — o título vira o nome do PDF e volta no afterprint', async () => {
    document.title = 'StartBig';
    const { imprimir, dadosParaImprimir } = useImprimirProposta({ detalhe: ref(detalheFixture()), gravarPendencias: async () => true });
    expect(await imprimir()).toBe(true);
    expect(imprimirComPagina).toHaveBeenCalledWith('A4', { folha: 'A4' });
    expect(document.title).toBe('Proposta ORC-2026-000001 v1 - Dona Marta');
    expect(dadosParaImprimir.value).not.toBeNull();
    window.dispatchEvent(new Event('afterprint'));
    expect(document.title).toBe('StartBig');
    expect(dadosParaImprimir.value).toBeNull();
  });

  it('16 — "Enviar e gerar proposta": envia ANTES de imprimir; com 422, nenhum dos dois termina', async () => {
    const ordem: string[] = [];
    imprimirComPagina.mockImplementation(() => ordem.push('imprimir'));
    const { enviarEImprimir } = useImprimirProposta({ detalhe: ref(detalheFixture()), gravarPendencias: async () => true });
    const enviado = { ...detalheFixture(), status: 'ENVIADO', datas: { ...detalheFixture().datas, validade: '2026-10-24' } } as Detalhe;
    await enviarEImprimir(async () => { ordem.push('enviar'); return enviado; });
    expect(ordem).toEqual(['enviar', 'imprimir']);
    window.dispatchEvent(new Event('afterprint'));

    imprimirComPagina.mockClear();
    const ok = await enviarEImprimir(async () => null);                // 422: faltou algo
    await flushPromises();
    expect(ok).toBe(false);
    expect(imprimirComPagina).not.toHaveBeenCalled();
  });
});
