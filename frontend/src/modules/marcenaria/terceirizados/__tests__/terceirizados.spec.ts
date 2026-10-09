/**
 * Spec 11B §11 — os móveis terceirizados na OS (seção "Móveis da central")
 * e a aba "Terceirizados" da tela de Serviços (casos 03-12; o 01 está em
 * OrdemServicoView.abas.spec.ts e o 02 em separacao.spec.ts).
 *
 * Os JSON de `fixtures/` são respostas REAIS da API da 11A, gerados por um
 * teste temporário do backend em 09/10/2026. No modo manual, a Torre Quente e
 * o Painel TV foram anotados com previsão 06/10 (3 dias antes): por isso o
 * relógio dos testes fica em 09/10/2026.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

// --- API simulada ----------------------------------------------------------------
const api = {
  getTerceirizados: vi.fn(),
  pedir: vi.fn(),
  enviarManual: vi.fn(),
  receberManual: vi.fn(),
  conferir: vi.fn(),
  registrarProblema: vi.fn(),
  voltar: vi.fn(),
  getTerceirizadosEmAberto: vi.fn(),
};
vi.mock('../services/terceirizado.service', () => ({
  getTerceirizados: (...a: unknown[]) => api.getTerceirizados(...a),
  pedir: (...a: unknown[]) => api.pedir(...a),
  enviarManual: (...a: unknown[]) => api.enviarManual(...a),
  receberManual: (...a: unknown[]) => api.receberManual(...a),
  conferir: (...a: unknown[]) => api.conferir(...a),
  registrarProblema: (...a: unknown[]) => api.registrarProblema(...a),
  voltar: (...a: unknown[]) => api.voltar(...a),
  getTerceirizadosEmAberto: (...a: unknown[]) => api.getTerceirizadosEmAberto(...a),
}));
const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() };
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => toast }));
// O Compras (módulo + permissões) é simulado: cada teste diz o que a pessoa pode.
const comprasVer = ref(false);
const comprasGerir = ref(false);
vi.mock('@/modules/compras/shared/composables/useAcessoCompras', () => ({
  useAcessoCompras: () => ({ podeVer: comprasVer, podeGerenciar: comprasGerir }),
}));
const router = { push: vi.fn() };
vi.mock('vue-router', async (original) => ({ ...(await original<typeof import('vue-router')>()), useRouter: () => router }));
const abrirOS = vi.fn();
vi.mock('@/modules/marcenaria/orcamentos/composables/useAbrirOS', () => ({
  useAbrirOS: () => ({ abrirOS, abrindo: ref(false) }),
}));

const { default: SecaoTerceirizados } = await import('../components/SecaoTerceirizados.vue');
const { default: TerceirizadoLinha } = await import('../components/TerceirizadoLinha.vue');
const { default: TerceirizadosTab } = await import('../components/TerceirizadosTab.vue');
const schemas = await import('../schemas/terceirizado.schema');
const utils = await import('../utils/terceirizados');
const { agruparPorCentral } = await import('../composables/useTerceirizadosEmAberto');
const { novoQueryClient } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');
const fixtures = {
  manual: (await import('./fixtures/terceirizados-manual.json')).default,
  compras: (await import('./fixtures/terceirizados-compras.json')).default,
  semCustos: (await import('./fixtures/terceirizados-sem-custos.json')).default,
  pedir: (await import('./fixtures/pedir.json')).default,
  lista: (await import('./fixtures/lista-geral.json')).default,
};

type Secao = ReturnType<typeof schemas.terceirizadosSchema.parse>;
/** Uma cópia nova (e conferida pelo zod) da resposta real. */
const secao = (dados: unknown = fixtures.manual): Secao => schemas.terceirizadosSchema.parse(structuredClone(dados));
const movel = (dados: Secao, nome: string) => dados.moveis.find((m) => m.nome === nome)!;
const plugins = () => [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never;

const montados: ReturnType<typeof mount>[] = [];
async function montarSecao(dados: unknown = fixtures.manual) {
  api.getTerceirizados.mockResolvedValue(secao(dados));
  const w = mount(SecaoTerceirizados, { props: { numeroOs: 'OS-2026-000001' }, attachTo: document.body, global: { plugins: plugins() } });
  montados.push(w);
  await flushPromises();
  return w;
}
const corpo = () => document.body.textContent ?? '';
const el = (testid: string) => document.body.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;
const botao = (testid: string) => el(testid)?.closest('button') ?? (el(testid) as HTMLButtonElement | null);
async function clicar(testid: string) {
  el(testid)!.click();
  await flushPromises();
}
async function marcar(movelId: number) {
  const caixa = el(`marcar-${movelId}`) as HTMLInputElement;
  caixa.checked = !caixa.checked;
  caixa.dispatchEvent(new Event('change'));
  await flushPromises();
}
/** O `title` do invólucro do botão: o motivo de estar apagado (D3). */
const motivo = (testid: string) => el(testid)!.closest('span[title]')?.getAttribute('title') ?? null;

beforeEach(() => {
  for (const f of [...Object.values(api), ...Object.values(toast), router.push, abrirOS]) f.mockReset();
  comprasVer.value = false;
  comprasGerir.value = false;
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date(2026, 9, 9, 10, 0));          // 09/10/2026, o dia em que as fixtures nasceram
});
afterEach(() => {
  montados.splice(0).forEach((w) => w.unmount());
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('respostas reais da 11A', () => {
  it('seção (manual, Compras, sem custos), pedido e lista geral passam no zod', () => {
    for (const dados of [fixtures.manual, fixtures.compras, fixtures.semCustos]) schemas.terceirizadosSchema.parse(dados);
    expect(schemas.pedirRespostaSchema.parse(fixtures.pedir).pedido.codigo).toBe('PC-000001');
    expect(schemas.listaTerceirizadosSchema.parse(fixtures.lista).itens).toHaveLength(5);
  });
});

describe('regras da barra de ações (D3)', () => {
  const dados = secao();

  it('03 — pedir com centrais diferentes: "Marque móveis da mesma central."', () => {
    // Ilha (Central Norte) + Torre Quente (Madeiranit)
    const r = utils.podeAplicar('pedir', [movel(dados, 'Ilha'), movel(dados, 'Torre Quente')]);
    expect(r).toEqual({ ok: false, motivo: 'Marque móveis da mesma central.' });
  });

  it('04 — conferir com um "A pedir" marcado: motivo de situação', () => {
    const r = utils.podeAplicar('conferir', [movel(dados, 'Aéreo'), movel(dados, 'Ilha')]);
    expect(r).toEqual({ ok: false, motivo: 'Só móveis "Recebido".' });
  });

  it('nada marcado, e o caso que pode', () => {
    expect(utils.podeAplicar('receber', []).motivo).toBe('Marque pelo menos um móvel.');
    expect(utils.podeAplicar('receber', [movel(dados, 'Torre Quente'), movel(dados, 'Painel TV')])).toEqual({ ok: true });
    // Conferir não exige a mesma central (não cria pedido).
    expect(utils.podeAplicar('conferir', [movel(dados, 'Aéreo')])).toEqual({ ok: true });
  });

  it('móvel com pedido em rascunho no Compras não é pedido de novo', () => {
    const compras = secao(fixtures.compras);
    expect(utils.podeAplicar('pedir', [movel(compras, 'Torre Quente')]).motivo).toBe('Há móvel com pedido em rascunho no Compras.');
  });

  it('voltar um passo: para onde vai (no Compras, só do Conferido)', () => {
    expect(utils.voltaPara(movel(dados, 'Nicho'))).toBe('RECEBIDO');
    expect(utils.voltaPara(movel(dados, 'Aéreo'))).toBe('ENVIADO');
    expect(utils.voltaPara(movel(dados, 'Torre Quente'))).toBe('A_PEDIR');
    expect(utils.voltaPara(movel(dados, 'Ilha'))).toBeNull();
    expect(utils.voltaPara(movel(secao(fixtures.compras), 'Painel TV'))).toBeNull();
  });

  it('hojeIso usa o relógio da loja, não o UTC (23h30 ainda é hoje)', () => {
    expect(utils.hojeIso(new Date(2026, 9, 9, 23, 30))).toBe('2026-10-09');
  });
});

describe('seção "Móveis da central" na OS', () => {
  it('título com a contagem e os atrasados; agrupada por central com o telefone (D1, D2)', async () => {
    await montarSecao();
    expect(el('titulo-terceirizados')!.textContent).toContain('Móveis da central (5) · 2 atrasados');
    expect(el('central-1')!.textContent).toContain('Madeiranit · (85) 99999-0000');
    expect(el('central-2')!.textContent).toContain('Central Norte');
    // O pedido com a previsão, como quem liga para a central precisa ver.
    expect(el('terceirizado-1')!.textContent).toContain('Pedido 4521 · chega 06/10');
    expect(el('terceirizado-4')!.textContent).toContain('Recebido com problema');
    expect(el('terceirizado-4')!.textContent).toContain('Problema: Porta riscada');
  });

  it('05 — com o Compras e permissão de gerir: "Pedir à central", sem os manuais', async () => {
    comprasGerir.value = true;
    await montarSecao(fixtures.compras);
    expect(el('acao-pedir')).not.toBeNull();
    expect(el('acao-enviar')).toBeNull();
    expect(el('acao-receber')).toBeNull();
    expect(el('acao-conferir')).not.toBeNull();
    expect(el('dica-conta')).toBeNull();
    // A linha do Compras: "Pedido em rascunho" e o código do pedido.
    expect(el('terceirizado-6')!.textContent).toContain('Pedido em rascunho');
    expect(el('terceirizado-6')!.textContent).toContain('PC-000001');
  });

  it('05b — com o Compras mas SEM permissão de gerir: nem pedir, nem os manuais', async () => {
    await montarSecao(fixtures.compras);
    expect(el('acao-pedir')).toBeNull();
    expect(el('acao-enviar')).toBeNull();
    expect(el('acao-conferir')).not.toBeNull();
  });

  it('06 — sem o Compras: "Enviar pedido", "Receber" e a dica da conta', async () => {
    await montarSecao();
    expect(el('acao-pedir')).toBeNull();
    expect(el('acao-enviar')).not.toBeNull();
    expect(el('acao-receber')).not.toBeNull();
    expect(el('dica-conta')!.textContent).toContain('Lance a conta da central em Contas a Pagar, numa categoria de despesa.');
  });

  it('os botões só habilitam com a seleção certa, e o title diz por quê (D3)', async () => {
    await montarSecao();
    expect(botao('acao-receber')!.disabled).toBe(true);
    expect(motivo('acao-receber')).toBe('Marque pelo menos um móvel.');
    await marcar(1);                                          // Torre Quente, Pedido enviado
    expect(botao('acao-receber')!.disabled).toBe(false);
    await marcar(3);                                          // + Ilha, de outra central
    expect(botao('acao-receber')!.disabled).toBe(true);
    expect(motivo('acao-receber')).toBe('Marque móveis da mesma central.');
  });

  it('07 — pedido criado: toast com "Abrir pedido PC-…", que leva aos rascunhos do Compras', async () => {
    comprasGerir.value = true;
    const inicio = secao(fixtures.compras);
    inicio.moveis[0].pedido = null;                           // Torre Quente ainda sem pedido
    const w = await montarSecao(inicio);
    api.pedir.mockResolvedValue(schemas.pedirRespostaSchema.parse(structuredClone(fixtures.pedir)));

    await marcar(6);
    await clicar('acao-pedir');
    expect(corpo()).toContain('O pedido nasce como rascunho no Compras. Envie e receba por lá.');
    await clicar('confirmar-pedir');

    expect(api.pedir).toHaveBeenCalledWith('OS-2026-000001', [6], null, null);
    expect(toast.success).toHaveBeenCalledTimes(1);
    const [mensagem, , opcoes] = toast.success.mock.calls[0];
    expect(mensagem).toBe('Pedido PC-000001 criado no Compras.');
    expect(opcoes.action.label).toBe('Abrir pedido PC-000001');
    // O clique no toast pede ao pai (o modal de OS) para fechar e ir.
    opcoes.action.onClick();
    expect(w.emitted('navegar')![0]).toEqual([{ name: 'purchases-orders', query: { situacao: 'RASCUNHO' } }]);
    // A tela já mostra o que a API devolveu, e a seleção foi limpa.
    expect(el('terceirizado-6')!.textContent).toContain('Pedido em rascunho');
    expect((el('marcar-6') as HTMLInputElement).checked).toBe(false);
  });

  it('o toast clicado depois de a aba fechar: o próprio roteador leva', async () => {
    comprasGerir.value = true;
    const inicio = secao(fixtures.compras);
    inicio.moveis[0].pedido = null;
    const w = await montarSecao(inicio);
    api.pedir.mockResolvedValue(schemas.pedirRespostaSchema.parse(structuredClone(fixtures.pedir)));
    await marcar(6);
    await clicar('acao-pedir');
    await clicar('confirmar-pedir');
    w.unmount();
    montados.splice(montados.indexOf(w), 1);
    toast.success.mock.calls[0][2].action.onClick();
    expect(router.push).toHaveBeenCalledWith({ name: 'purchases-orders', query: { situacao: 'RASCUNHO' } });
  });

  it('08 — "Pedido enviado" do Compras: "Ver no Compras" leva ao recebimento do pedido', async () => {
    comprasVer.value = true;
    const w = await montarSecao(fixtures.compras);
    el('terceirizado-7')!.querySelector<HTMLButtonElement>('[data-testid="ver-no-compras"]')!.click();
    el('terceirizado-6')!.querySelector<HTMLButtonElement>('[data-testid="ver-no-compras"]')!.click();
    expect(w.emitted('navegar')).toEqual([
      [{ name: 'purchases-receiving', query: { pedido: '2' } }],
      [{ name: 'purchases-orders', query: { situacao: 'RASCUNHO' } }],
    ]);
  });

  it('"Ver no Compras" some para quem não vê o Compras (e no modo manual)', async () => {
    await montarSecao(fixtures.compras);
    expect(el('ver-no-compras')).toBeNull();
  });

  it('enviar à mão: nº e previsão opcionais', async () => {
    await montarSecao();
    api.enviarManual.mockResolvedValue(secao());
    await marcar(3);                                          // Ilha, A pedir
    await clicar('acao-enviar');
    const campo = el('numero-pedido') as HTMLInputElement;
    campo.value = ' 777 ';
    campo.dispatchEvent(new Event('input'));
    await clicar('confirmar-enviar');
    expect(api.enviarManual).toHaveBeenCalledWith('OS-2026-000001', [3], '777', null);
    expect(toast.success).toHaveBeenCalledWith('Pedido à central anotado.');
  });

  it('receber à mão: a data já vem com hoje', async () => {
    await montarSecao();
    api.receberManual.mockResolvedValue(secao());
    await marcar(1);
    await marcar(2);
    await clicar('acao-receber');
    await clicar('confirmar-receber');
    expect(api.receberManual).toHaveBeenCalledWith('OS-2026-000001', [1, 2], '2026-10-09');
  });

  it('conferir: grava e avisa o pai quando a OS ganha sugestão de status (12B)', async () => {
    const w = await montarSecao();
    const resposta = secao();
    resposta.sugestao_status = { de: 'ABERTA', para: 'AGUARDANDO_ENTREGA', rotulo: 'Pronta para entrega' };
    api.conferir.mockResolvedValue(resposta);
    await marcar(4);                                          // Aéreo, Recebido
    await clicar('acao-conferir');
    expect(api.conferir).toHaveBeenCalledWith('OS-2026-000001', [4]);
    expect(w.emitted('sugestaoStatus')).toHaveLength(1);
  });

  it('erro na ação: toast com a frase da API e o modal fica aberto', async () => {
    await montarSecao();
    api.enviarManual.mockRejectedValue(new Error('rede'));
    await marcar(3);
    await clicar('acao-enviar');
    await clicar('confirmar-enviar');
    expect(toast.error).toHaveBeenCalled();
    expect(el('confirmar-enviar')).not.toBeNull();
  });

  it('registrar problema pelo menu da linha', async () => {
    await montarSecao();
    api.registrarProblema.mockResolvedValue(secao());
    el('terceirizado-5')!.querySelector<HTMLButtonElement>('[data-testid="menu-5"]')!.click();
    await flushPromises();
    await clicar('opcao-problema');
    const campo = el('texto-problema') as HTMLTextAreaElement;
    campo.value = 'Gaveta empenada';
    campo.dispatchEvent(new Event('input'));
    await flushPromises();                                    // o botão só habilita com texto
    await clicar('confirmar-problema');
    expect(api.registrarProblema).toHaveBeenCalledWith('OS-2026-000001', 5, 'Gaveta empenada');
  });

  it('10 — voltar um passo de "Conferido": confirmação "Voltar para Recebido?"', async () => {
    await montarSecao();
    api.voltar.mockResolvedValue(secao());
    el('terceirizado-5')!.querySelector<HTMLButtonElement>('[data-testid="menu-5"]')!.click();
    await flushPromises();
    await clicar('opcao-voltar');
    expect(corpo()).toContain('Voltar para Recebido?');
    expect(corpo()).toContain('volta de "Conferido" para "Recebido"');
    expect(api.voltar).not.toHaveBeenCalled();               // só depois de confirmar
    const confirmar = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Voltar')!;
    confirmar.click();
    await flushPromises();
    expect(api.voltar).toHaveBeenCalledWith('OS-2026-000001', 5);
  });

  it('com um modal aberto, a seção avisa a aba (o leitor de código dorme)', async () => {
    const w = await montarSecao();
    await marcar(3);
    await clicar('acao-enviar');
    const avisos = w.emitted('update:ocupado')!;
    expect(avisos[avisos.length - 1]).toEqual([true]);
  });

  it('OS fechada: só leitura, sem caixas, barra nem menu (D9)', async () => {
    const fechada = structuredClone(fixtures.manual);
    fechada.os.editavel = false;
    await montarSecao(fechada);
    expect(el('secao-terceirizados')).not.toBeNull();
    expect(el('marcar-1')).toBeNull();
    expect(el('barra-terceirizados')).toBeNull();
    expect(el('menu-5')).toBeNull();
  });

  it('OS sem móvel terceirizado: a seção não aparece', async () => {
    const vazia = structuredClone(fixtures.manual);
    vazia.moveis = [];
    await montarSecao(vazia);
    expect(el('secao-terceirizados')).toBeNull();
  });

  it('12 — sem view_custos_marcenaria: sem valor orçado', async () => {
    await montarSecao(fixtures.semCustos);
    expect(el('valor-orcado')).toBeNull();
  });

  it('com custos: o valor orçado da central em cinza (D8)', async () => {
    await montarSecao();
    expect(el('terceirizado-1')!.querySelector('[data-testid="valor-orcado"]')!.textContent).toMatch(/orçado R\$\s*380,00/);
  });
});

describe('TerceirizadoLinha', () => {
  it('09 — atrasado 3 dias: selo "Atrasado 3 dias"', () => {
    const w = mount(TerceirizadoLinha, {
      props: { movel: movel(secao(), 'Torre Quente'), editavel: true, marcado: false, verNoCompras: false },
    });
    montados.push(w);
    expect(w.get('[data-testid="atraso"]').text()).toBe('Atrasado 3 dias');
  });

  it('sem atraso: sem selo vermelho', () => {
    const w = mount(TerceirizadoLinha, {
      props: { movel: movel(secao(), 'Ilha'), editavel: true, marcado: false, verNoCompras: false },
    });
    montados.push(w);
    expect(w.find('[data-testid="atraso"]').exists()).toBe(false);
    expect(w.get('[data-testid="selo"]').text()).toBe('A pedir');
  });
});

describe('aba "Terceirizados" em Serviços', () => {
  const lista = () => schemas.listaTerceirizadosSchema.parse(structuredClone(fixtures.lista)).itens;

  async function montarAba() {
    // A API filtra (11A D17); a simulação devolve o que ela devolveria.
    api.getTerceirizadosEmAberto.mockImplementation(async (f: { situacao?: string | null; atrasados?: boolean }) =>
      lista().filter((i) => (!f.situacao || i.situacao === f.situacao) && (!f.atrasados || i.atrasado)));
    const w = mount(TerceirizadosTab, { attachTo: document.body, global: { plugins: plugins() } });
    montados.push(w);
    await flushPromises();
    return w;
  }

  it('11 — padrão: só "Pedido enviado", agrupado por central, com telefone e contagem (D11, D12)', async () => {
    await montarAba();
    expect(api.getTerceirizadosEmAberto).toHaveBeenCalledWith({ situacao: 'ENVIADO', atrasados: false });
    expect((el('filtro-situacao') as HTMLSelectElement).value).toBe('ENVIADO');
    // Só a Madeiranit tem móvel enviado: um pedido (4521) cobrindo dois móveis atrasados.
    expect(el('grupo-1')!.textContent).toContain('Madeiranit');
    expect(el('grupo-1')!.textContent).toContain('(85) 99999-0000');
    expect(el('resumo-grupo')!.textContent).toContain('1 pedido, 2 atrasados');
    expect(el('grupo-2')).toBeNull();
    expect(el('item-1')!.textContent).toContain('Dona Marta');
    expect(el('item-1')!.textContent).toContain('Pedido 4521');
    expect(el('item-1')!.querySelector('[data-testid="atraso"]')!.textContent).toContain('3 dias');
  });

  it('"Todas" mostra as duas centrais; o número da OS abre a OS', async () => {
    await montarAba();
    const filtro = el('filtro-situacao') as HTMLSelectElement;
    filtro.value = '';
    filtro.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(api.getTerceirizadosEmAberto).toHaveBeenLastCalledWith({ situacao: null, atrasados: false });
    expect(el('grupo-2')!.textContent).toContain('Central Norte');
    await clicar('abrir-os-3');
    expect(abrirOS).toHaveBeenCalledWith('OS-2026-000001');
  });

  it('"Só atrasados" vai para a API', async () => {
    await montarAba();
    const caixa = el('filtro-atrasados') as HTMLInputElement;
    caixa.checked = true;
    caixa.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(api.getTerceirizadosEmAberto).toHaveBeenLastCalledWith({ situacao: 'ENVIADO', atrasados: true });
  });

  it('agruparPorCentral conta pedidos diferentes, não móveis', () => {
    const grupos = agruparPorCentral(lista());
    expect(grupos.map((g) => [g.nome, g.itens.length, g.pedidos, g.atrasados])).toEqual([
      ['Madeiranit', 3, 2, 2],                                // 4521 (2 móveis) + 4522
      ['Central Norte', 2, 1, 0],                             // Ilha sem pedido; Nicho anotado sem número
    ]);
  });
});
