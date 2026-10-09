/**
 * Spec 10B §11 — a aba Separação da OS da marcenaria (casos 03-16; os casos
 * 01-02 das abas estão em OSFormAbasOrcamento.spec.ts).
 *
 * Os JSON de `fixtures/` são respostas REAIS da API da 10A (cenário B
 * aprovado; MDF com 2 chapas no estoque para 3 sugeridas; corrediça toda
 * retirada), gerados por um teste temporário do backend.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';

// --- API simulada ----------------------------------------------------------------
const getSeparacao = vi.fn();
const retirar = vi.fn();
const concluir = vi.fn();
const lerCodigo = vi.fn();
const getFaltas = vi.fn();
const getDisponivel = vi.fn();
vi.mock('../services/separacao.service', async (original) => ({
  ...(await original<typeof import('../services/separacao.service')>()),
  getSeparacao: (...a: unknown[]) => getSeparacao(...a),
  retirar: (...a: unknown[]) => retirar(...a),
  concluir: (...a: unknown[]) => concluir(...a),
  lerCodigo: (...a: unknown[]) => lerCodigo(...a),
  getFaltas: (...a: unknown[]) => getFaltas(...a),
  getDisponivel: (...a: unknown[]) => getDisponivel(...a),
}));
const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() };
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => toast }));
// O módulo Compras (D19) e o texto do status da OS (01B) são simulados.
const comCompras = ref(false);
vi.mock('@/modules/compras/shared/composables/useAcessoCompras', () => ({ useAcessoCompras: () => ({ podeVer: comCompras }) }));
vi.mock('@/modules/order-service/shared/segmento/useRotulosStatusOS', () => ({
  useRotulosStatusOS: () => ({ rotuloStatus: (s: string) => ({ FINALIZADA: 'Finalizada', CANCELADA: 'Cancelada' }[s] ?? s) }),
}));
const getProdutos = vi.fn();
vi.mock('@/modules/products/inventory/services/product.service', () => ({ getProdutos: (...a: unknown[]) => getProdutos(...a) }));

const { default: OSSeparacaoTab } = await import('../components/OSSeparacaoTab.vue');
const { default: FaltasDaOS } = await import('../components/FaltasDaOS.vue');
const { default: FaltasPrint } = await import('../components/FaltasPrint.vue');
const { default: InsumoBusca } = await import('@/modules/marcenaria/orcamentos/components/modais/InsumoBusca.vue');
const { useLeitorCodigo } = await import('../composables/useLeitorCodigo');
const schemas = await import('../schemas/separacao.schema');
const { novoQueryClient } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');
const fixtures = {
  separacao: (await import('./fixtures/separacao.json')).default,
  semCadastro: (await import('./fixtures/separacao-sem-cadastro.json')).default,
  finalizada: (await import('./fixtures/separacao-finalizada.json')).default,
  leituraMdf: (await import('./fixtures/leitura-mdf.json')).default,
  leituraCaixa: (await import('./fixtures/leitura-caixa.json')).default,
  faltas: (await import('./fixtures/faltas.json')).default,
  faltasVazia: (await import('./fixtures/faltas-vazia.json')).default,
  disponivel: (await import('./fixtures/disponivel.json')).default,
};

type Separacao = ReturnType<typeof schemas.separacaoSchema.parse>;
const separacao = (): Separacao => schemas.separacaoSchema.parse(structuredClone(fixtures.separacao));
const plugins = () => [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never;

/** Erro do axios com resposta (404, 409...). */
function erroApi(status: number, detail: unknown): AxiosError {
  const resposta = { status, data: { detail }, statusText: '', headers: {}, config: { headers: new AxiosHeaders() } } as AxiosResponse;
  return new AxiosError('erro', 'ERR_BAD_RESPONSE', undefined, undefined, resposta);
}

const montados: ReturnType<typeof mount>[] = [];
async function montarAba(dados: unknown = fixtures.separacao) {
  getSeparacao.mockResolvedValue(schemas.separacaoSchema.parse(structuredClone(dados)));
  const w = mount(OSSeparacaoTab, { props: { numeroOs: 'OS-2026-000001' }, attachTo: document.body, global: { plugins: plugins() } });
  montados.push(w);
  await flushPromises();
  return w;
}
const corpo = () => document.body.textContent ?? '';
const el = (testid: string) => document.body.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;

beforeEach(() => {
  for (const f of [getSeparacao, retirar, concluir, lerCodigo, getFaltas, getDisponivel, getProdutos, ...Object.values(toast)]) f.mockReset();
  comCompras.value = false;
});
afterEach(() => {
  montados.splice(0).forEach((w) => w.unmount());
  vi.restoreAllMocks();
  document.body.innerHTML = '';
});

describe('respostas reais da 10A', () => {
  it('separação, leitor, faltas e disponível passam no zod', () => {
    for (const dados of [fixtures.separacao, fixtures.semCadastro, fixtures.finalizada]) schemas.separacaoSchema.parse(dados);
    schemas.leituraSchema.parse(fixtures.leituraMdf);
    expect(schemas.leituraSchema.parse(fixtures.leituraCaixa).fator).toBe(10);
    schemas.faltasSchema.parse(fixtures.faltas);
    schemas.faltasSchema.parse(fixtures.faltasVazia);
    expect(schemas.disponivelSchema.parse(fixtures.disponivel)['1'].disponivel_milesimos).toBe(-1000);
  });
});

describe('useLeitorCodigo (D14, D17)', () => {
  /** Simula as teclas com o relógio de `performance.now()` controlado. */
  function digitar(texto: string, intervaloMs: number, alvo: EventTarget = document) {
    let agora = 1000;
    vi.spyOn(performance, 'now').mockImplementation(() => agora);
    for (const tecla of [...texto, 'Enter']) {
      alvo.dispatchEvent(new KeyboardEvent('keydown', { key: tecla, bubbles: true }));
      agora += intervaloMs;
    }
  }
  function montarLeitor(ativo = true, ignorar: HTMLElement | null = null) {
    const aoLer = vi.fn();
    const Teste = defineComponent({ setup() { useLeitorCodigo(aoLer, ref(ativo), ref(ignorar)); return () => h('div'); } });
    montados.push(mount(Teste));
    return aoLer;
  }

  it('03 — "7891234" em 10 ms por tecla + Enter: uma leitura', () => {
    const aoLer = montarLeitor();
    digitar('7891234', 10);
    expect(aoLer).toHaveBeenCalledTimes(1);
    expect(aoLer).toHaveBeenCalledWith('7891234');
  });

  it('04 — digitado devagar (200 ms entre teclas): o ouvinte global não lê', () => {
    const aoLer = montarLeitor();
    digitar('7891234', 200);
    expect(aoLer).not.toHaveBeenCalled();
  });

  it('05 — com `ativo = false` (aba fechada ou modal aberto): não lê', () => {
    const aoLer = montarLeitor(false);
    digitar('7891234', 10);
    expect(aoLer).not.toHaveBeenCalled();
  });

  it('o que é digitado DENTRO do campo é do campo (não lê duas vezes)', () => {
    const campo = document.createElement('input');
    document.body.appendChild(campo);
    const aoLer = montarLeitor(true, campo);
    digitar('7891234', 10, campo);
    expect(aoLer).not.toHaveBeenCalled();
  });
});

describe('aba Separação', () => {
  it('ordem do depósito, só pendentes por padrão, progresso e faltas (D2, D3)', async () => {
    const w = await montarAba();
    expect(corpo()).toContain('MDF Branco TX 18mm');
    expect(corpo()).toContain('Corredor A · Prateleira 2');
    expect(corpo()).not.toContain('Corrediça Tandem');                      // concluída: escondida
    expect(el('progresso')!.textContent).toContain('1 de 2 separados');
    expect(el('abrir-faltas')!.textContent).toContain('Faltas desta OS (1)');
    expect(el('sugerido')!.textContent).toBe('3 un');
    expect(el('no-estoque')!.textContent!.trim()).toBe('2 un');
    expect(corpo()).toContain('Falta no estoque');                          // SEM_COBERTURA
    expect(corpo()).toContain('Balcão 2,2');
    expect(document.activeElement).toBe(el('campo-codigo'));                // D2: focado ao abrir

    await w.find('[data-testid="so-pendentes"]').setValue(false);
    expect(el('linha-concluida')!.textContent).toContain('Retirado 6 par');
    expect(corpo()).not.toMatch(/R\$/);                                     // D9: nenhum preço
  });

  it('06 — produto de fora: mensagem, som, campo limpo e focado', async () => {
    lerCodigo.mockRejectedValue(erroApi(404, 'Este produto não faz parte desta OS.'));
    const w = await montarAba();
    const campo = w.find('[data-testid="campo-codigo"]');
    await campo.setValue('9999999');
    await campo.trigger('keydown', { key: 'Enter' });
    await flushPromises();
    expect(el('mensagem-leitor')!.textContent).toContain('Este produto não faz parte desta OS.');
    expect((campo.element as HTMLInputElement).value).toBe('');
    expect(document.activeElement).toBe(campo.element);
  });

  it('14 (D14) — bipe abre o Retirar com o que falta; Enter confirma', async () => {
    lerCodigo.mockResolvedValue(schemas.leituraSchema.parse(structuredClone(fixtures.leituraMdf)));
    retirar.mockResolvedValue(separacao());
    const w = await montarAba();
    const campo = w.find('[data-testid="campo-codigo"]');
    await campo.setValue('7891000000018');
    await campo.trigger('keydown', { key: 'Enter' });
    await flushPromises();
    const quantidade = el('quantidade-retirar') as HTMLInputElement;
    expect(quantidade.value).toBe('3');
    quantidade.form!.dispatchEvent(new Event('submit'));
    await flushPromises();
    expect(retirar).toHaveBeenCalledWith('OS-2026-000001', 5, 3000, 0);     // item, quantidade, a trava
  });

  it('07 — "cada leitura retira": UN retira 1, a caixa de 10 retira 10, metro abre o modal', async () => {
    retirar.mockResolvedValue(separacao());
    const w = await montarAba();
    await w.find('[data-testid="cada-leitura-retira"]').setValue(true);
    const ler = async () => {
      const campo = w.find('[data-testid="campo-codigo"]');
      await campo.setValue('codigo');
      await campo.trigger('keydown', { key: 'Enter' });
      await flushPromises();
    };

    lerCodigo.mockResolvedValue(schemas.leituraSchema.parse(structuredClone(fixtures.leituraMdf)));
    await ler();
    expect(retirar).toHaveBeenLastCalledWith('OS-2026-000001', 5, 1000, 0);

    const caixa = structuredClone(fixtures.leituraCaixa);                   // a corrediça ainda pendente
    Object.assign(caixa.linha, { concluida: false, separada_milesimos: 0, falta_milesimos: 6000 });
    lerCodigo.mockResolvedValue(schemas.leituraSchema.parse(caixa));
    await ler();
    expect(retirar).toHaveBeenLastCalledWith('OS-2026-000001', 4, 10000, 0);

    const metro = structuredClone(fixtures.leituraMdf);
    metro.linha.unidade = 'M';
    lerCodigo.mockResolvedValue(schemas.leituraSchema.parse(metro));
    retirar.mockClear();
    await ler();
    expect(retirar).not.toHaveBeenCalled();
    expect(el('quantidade-retirar')).not.toBeNull();                        // o modal abriu
  });

  it('15 (D15) — linha já concluída: "Este item já foi separado."', async () => {
    lerCodigo.mockResolvedValue(schemas.leituraSchema.parse(structuredClone(fixtures.leituraCaixa)));
    const w = await montarAba();
    const campo = w.find('[data-testid="campo-codigo"]');
    await campo.setValue('17891000000025');
    await campo.trigger('keydown', { key: 'Enter' });
    await flushPromises();
    expect(el('mensagem-leitor')!.textContent).toContain('Este item já foi separado.');
    expect(el('quantidade-retirar')).toBeNull();
  });

  it('08 — estoque não cobre: aviso âmbar e "Retirar mesmo assim"', async () => {
    const w = await montarAba();
    await w.find('[data-testid="acao-retirar"]').trigger('click');
    await flushPromises();
    expect(el('aviso-estoque')!.textContent).toContain('Estoque insuficiente para esta OS: há 2 un.');
    expect(el('confirmar-retirar')!.textContent).toContain('Retirar mesmo assim');
    const quantidade = el('quantidade-retirar') as HTMLInputElement;
    quantidade.value = '4';
    quantidade.dispatchEvent(new Event('input'));
    await flushPromises();
    expect(el('aviso-acima')!.textContent).toContain('Acima do sugerido (3 un)');
    quantidade.value = '1,5';
    quantidade.dispatchEvent(new Event('input'));
    await flushPromises();
    expect(corpo()).toContain('Esta unidade não aceita fração');
  });

  it('09 — 409 ao retirar: aviso, recarrega e não tenta de novo', async () => {
    retirar.mockRejectedValue(erroApi(409, { codigo: 'REVISAO_DESATUALIZADA', mensagem: 'x' }));
    const w = await montarAba();
    expect(getSeparacao).toHaveBeenCalledTimes(1);
    await w.find('[data-testid="acao-retirar"]').trigger('click');
    await flushPromises();
    (el('confirmar-retirar') as HTMLButtonElement).click();
    await flushPromises();
    expect(toast.error).toHaveBeenCalledWith('Outra pessoa alterou este item. A lista foi atualizada.');
    expect(retirar).toHaveBeenCalledTimes(1);
    expect(getSeparacao).toHaveBeenCalledTimes(2);                          // recarregou
  });

  it('10 — OS finalizada: sem botões e com a frase', async () => {
    await montarAba(fixtures.finalizada);
    expect(el('separacao-fechada')!.textContent).toContain('A OS está finalizada: a separação não pode mais ser alterada.');
    expect(el('acao-retirar')).toBeNull();
    expect(el('campo-codigo')).toBeNull();
  });

  it('11 — produto excluído do cadastro: bloco cinza, sem botões', async () => {
    await montarAba(fixtures.semCadastro);
    const bloco = el('sem-cadastro')!;
    expect(bloco.textContent).toContain('Produto excluído do cadastro: não baixa estoque');
    expect(bloco.textContent).toContain('Puxador perfil antigo · 2');
    expect(bloco.querySelector('button')).toBeNull();
  });

  it('16 — concluir com 2 de 3: confirmação com o efeito; depois "Retirado 2 un"', async () => {
    const dados = structuredClone(fixtures.separacao);
    Object.assign(dados.linhas[0], { separada_milesimos: 2000, falta_milesimos: 1000 });
    const concluida = structuredClone(dados);
    Object.assign(concluida.linhas[0], { concluida: true, quantidade_milesimos: 2000, falta_milesimos: 0 });
    concluir.mockResolvedValue(schemas.separacaoSchema.parse(concluida));
    const w = await montarAba(dados);
    await w.find('[data-testid="so-pendentes"]').setValue(false);
    await w.find('[data-testid="linha-5"] [data-testid="menu-linha"]').trigger('click');
    await w.find('[data-testid="opcao-concluir"]').trigger('click');
    await flushPromises();
    expect(corpo()).toContain('a OS passa a consumir 2 un (o que foi retirado). A finalização não baixará mais nada deste produto.');
    const confirmar = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Concluir')!;
    confirmar.click();
    await flushPromises();
    expect(concluir).toHaveBeenCalledWith('OS-2026-000001', 5, 2000);
    expect(el('linha-5')!.textContent).toContain('Retirado 2 un');
  });
});

describe('faltas desta OS (D18-D20)', () => {
  function montarFaltas(dados: unknown, compras = false) {
    getFaltas.mockResolvedValue(schemas.faltasSchema.parse(structuredClone(dados)));
    const w = mount(FaltasDaOS, {
      props: { isOpen: true, numeroOs: 'OS-2026-000001', temCompras: compras },
      attachTo: document.body, global: { plugins: plugins() },
    });
    montados.push(w);
    return w;
  }

  it('lista com o fornecedor para ligar', async () => {
    montarFaltas(fixtures.faltas);
    await flushPromises();
    expect(el('lista-faltas')!.textContent).toContain('MDF Branco TX 18mm');
    expect(el('lista-faltas')!.textContent).toContain('faltam 1 un');
    expect(el('lista-faltas')!.textContent).toContain('Madeireira Central');
  });

  it('12 — sem faltas: "Nada a comprar"', async () => {
    montarFaltas(fixtures.faltasVazia);
    await flushPromises();
    expect(el('sem-faltas')!.textContent).toContain('Nada a comprar: o estoque cobre esta OS.');
  });

  it('13 — "Ver nas Necessidades" só com o Compras', async () => {
    montarFaltas(fixtures.faltas, false);
    await flushPromises();
    expect(el('ver-necessidades')).toBeNull();
    montados.splice(0).forEach((w) => w.unmount());
    const w = montarFaltas(fixtures.faltas, true);
    await flushPromises();
    el('ver-necessidades')!.click();
    expect(w.emitted('verNecessidades')).toHaveLength(1);
  });

  it('14 — a folha impressa: só cores neutras e nenhum preço', () => {
    const w = mount(FaltasPrint, { props: { faltas: schemas.faltasSchema.parse(structuredClone(fixtures.faltas)) }, global: { plugins: plugins() } });
    montados.push(w);
    const folha = el('faltas-print')!;
    expect(folha.textContent).toContain('FALTAS DE MATERIAL');
    expect(folha.textContent).toContain('1 un');
    expect(folha.outerHTML).not.toMatch(/(red|amber|emerald|green|blue|brand|gray|slate)-\d|R\$/);
  });
});

describe('15 — disponível na busca de insumo (D21)', () => {
  it('"Estoque 2 un · faltam 1 un" em vermelho; positivo em cinza', async () => {
    getProdutos.mockResolvedValue([
      { id: 1, nome: 'MDF Branco TX 18mm', codigo_produto: 'P-1', unidade_medida: 'UN', sofre_perda: true },
      { id: 4, nome: 'Corrediça Tandem', codigo_produto: 'P-4', unidade_medida: 'PAR', sofre_perda: false },
    ]);
    getDisponivel.mockResolvedValue(schemas.disponivelSchema.parse(fixtures.disponivel));
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    const w = mount(InsumoBusca, { props: { produtosNoMovel: [], incluiCustos: false, podeCadastrar: false }, global: { plugins: plugins() } });
    montados.push(w);
    await w.find('[data-testid="busca-insumo"]').setValue('mdf');
    await vi.advanceTimersByTimeAsync(350);
    vi.useRealTimers();
    await flushPromises();
    expect(getDisponivel).toHaveBeenCalledWith([1, 4]);
    const mdf = w.find('[data-testid="disponivel-1"]');
    expect(mdf.text()).toBe('Estoque 2 un · faltam 1 un');
    expect(mdf.classes()).toContain('text-red-600');
    expect(w.find('[data-testid="disponivel-4"]').text()).toBe('Estoque 4 par · disponível 4 par');
  });
});
