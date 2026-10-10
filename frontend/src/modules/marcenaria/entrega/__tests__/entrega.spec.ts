/**
 * Spec 13B §11 — a aba Entrega da OS, o termo, a aba Instalações e o aviso
 * da finalização (casos 04-14; os casos 01-03 das abas estão em
 * OSFormAbasOrcamento.spec.ts e OrdemServicoView.abas.spec.ts).
 *
 * Os JSON de `fixtures/` são respostas REAIS da API da 13A, gerados por um
 * teste temporário do backend em 09/10/2026: OS com Cozinha Gourmet (entregue
 * com ressalvas, foto do termo e da montagem, uma pendência aberta e uma
 * resolvida), Sala e Closet pendentes; um agendamento amanhã (Cozinha + Sala,
 * Carlos e Davi) e outro ontem (Closet, atrasado). O relógio dos testes fica
 * em 09/10/2026, o dia em que as fixtures nasceram.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

// --- API simulada ----------------------------------------------------------------
const api = {
  getEntrega: vi.fn(), getResumo: vi.fn(), registrar: vi.fn(), enviarFoto: vi.fn(), excluirFoto: vi.fn(),
  editarChecklist: vi.fn(), criarPendencia: vi.fn(), resolverPendencia: vi.fn(), reabrirPendencia: vi.fn(),
  agendar: vi.fn(), editarAgendamento: vi.fn(), excluirAgendamento: vi.fn(), getInstalacoes: vi.fn(),
};
vi.mock('../services/entrega.service', async (original) => {
  const real = await original<typeof import('../services/entrega.service')>();
  return {
    ...real,
    getEntrega: (...a: unknown[]) => api.getEntrega(...a),
    getResumo: (...a: unknown[]) => api.getResumo(...a),
    registrar: (...a: unknown[]) => api.registrar(...a),
    enviarFoto: (...a: unknown[]) => api.enviarFoto(...a),
    excluirFoto: (...a: unknown[]) => api.excluirFoto(...a),
    editarChecklist: (...a: unknown[]) => api.editarChecklist(...a),
    criarPendencia: (...a: unknown[]) => api.criarPendencia(...a),
    resolverPendencia: (...a: unknown[]) => api.resolverPendencia(...a),
    reabrirPendencia: (...a: unknown[]) => api.reabrirPendencia(...a),
  };
});
vi.mock('../services/agenda.service', () => ({
  agendar: (...a: unknown[]) => api.agendar(...a),
  editarAgendamento: (...a: unknown[]) => api.editarAgendamento(...a),
  excluirAgendamento: (...a: unknown[]) => api.excluirAgendamento(...a),
  getInstalacoes: (...a: unknown[]) => api.getInstalacoes(...a),
}));
const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() };
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => toast }));
vi.mock('@/modules/order-service/shared/segmento/useRotulosStatusOS', () => ({
  useRotulosStatusOS: () => ({ rotuloStatus: (s: string) => ({ FINALIZADA: 'Finalizada', CANCELADA: 'Cancelada' }[s] ?? s) }),
}));
const abrirOS = vi.fn();
vi.mock('@/modules/marcenaria/orcamentos/composables/useAbrirOS', () => ({
  useAbrirOS: () => ({ abrirOS, abrindo: ref(false) }),
}));
// A impressão de verdade abre o diálogo do navegador: aqui só se registra o pedido.
const imprimirComPagina = vi.fn();
vi.mock('@/shared/utils/print.utils', async (original) => ({
  ...(await original<typeof import('@/shared/utils/print.utils')>()),
  imprimirComPagina: (...a: unknown[]) => imprimirComPagina(...a),
  aguardarImagensDaImpressao: async () => undefined,
}));

const { default: OSEntregaTab } = await import('../components/OSEntregaTab.vue');
const { default: RegistrarEntregaModal } = await import('../components/RegistrarEntregaModal.vue');
const { default: TermoEntregaPrint } = await import('../components/TermoEntregaPrint.vue');
const { default: InstalacoesTab } = await import('../components/InstalacoesTab.vue');
const { default: AvisoEntregaFinalizacao } = await import('../components/AvisoEntregaFinalizacao.vue');
const schemas = await import('../schemas/entrega.schema');
const utils = await import('../utils/entrega');
const { novoQueryClient } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');
const { default: fonteFinalizar } = await import('@/modules/order-service/ordens/components/OSFinalizarModal.vue?raw');
const fixtures = {
  entrega: (await import('./fixtures/entrega.json')).default,
  inicial: (await import('./fixtures/entrega-inicial.json')).default,
  fechada: (await import('./fixtures/entrega-fechada.json')).default,
  ocupado: (await import('./fixtures/agendar-ocupado.json')).default,
  semFoto: (await import('./fixtures/registrar-sem-foto.json')).default,
  ultimo: (await import('./fixtures/registrar-ultimo.json')).default,
  resumo: (await import('./fixtures/resumo.json')).default,
  instalacoes: (await import('./fixtures/instalacoes.json')).default,
};

type Entrega = ReturnType<typeof schemas.entregaDaOSSchema.parse>;
/** Uma cópia nova (e conferida pelo zod) da resposta real. */
const entrega = (dados: unknown = fixtures.entrega): Entrega => schemas.entregaDaOSSchema.parse(structuredClone(dados));
const ambiente = (dados: Entrega, nome: string) => dados.entregas.find((e) => e.ambiente === nome)!;
const plugins = () => [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never;
const FUNCIONARIOS = [{ id: 2, nome: 'Carlos' }, { id: 3, nome: 'Davi' }];

const montados: ReturnType<typeof mount>[] = [];
async function montarAba(dados: unknown = fixtures.entrega) {
  api.getEntrega.mockResolvedValue(entrega(dados));
  const w = mount(OSEntregaTab, {
    props: { numeroOs: 'OS-2026-000001', funcionarios: FUNCIONARIOS }, attachTo: document.body, global: { plugins: plugins() },
  });
  montados.push(w);
  await flushPromises();
  return w;
}
const corpo = () => document.body.textContent ?? '';
const el = (testid: string) => document.body.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;
async function clicar(testid: string) {
  el(testid)!.click();
  await flushPromises();
}
const botaoComTexto = (texto: string) =>
  [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === texto) as HTMLButtonElement | undefined;

beforeEach(() => {
  for (const f of [...Object.values(api), ...Object.values(toast), abrirOS, imprimirComPagina]) f.mockReset();
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date(2026, 9, 9, 10, 0));          // 09/10/2026, o dia em que as fixtures nasceram
});
afterEach(() => {
  montados.splice(0).forEach((w) => w.unmount());
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('respostas reais da 13A', () => {
  it('aba, resumo, avisos e instalações passam no zod', () => {
    for (const dados of [fixtures.entrega, fixtures.inicial, fixtures.fechada, fixtures.ocupado, fixtures.semFoto, fixtures.ultimo]) {
      schemas.entregaDaOSSchema.parse(dados);
    }
    expect(schemas.resumoSchema.parse(fixtures.resumo).ambientes_pendentes).toEqual(['Sala', 'Closet']);
    expect(schemas.instalacoesSchema.parse(fixtures.instalacoes).itens).toHaveLength(3);
  });
});

describe('regras de tela', () => {
  const dados = entrega();

  it('resumo, checklist e agendamento em frase', () => {
    expect(utils.textoDoResumo(dados.resumo)).toBe('1 de 3 ambientes entregues · 1 pendência aberta');
    expect(utils.resumoDoChecklist(ambiente(dados, 'Cozinha Gourmet').checklist)).toBe('3 ok · 1 não ok');
    expect(utils.resumoDoChecklist(ambiente(dados, 'Sala').checklist)).toBe('sem marcações');
    expect(utils.textoDoAgendamento(ambiente(dados, 'Sala').agendamento!)).toBe('Instalação 10/10 às 08:00 · Carlos, Davi');
  });

  it('períodos da aba Instalações (semana = segunda a domingo) e o título do dia', () => {
    expect(utils.datasDoPeriodo('amanha')).toEqual({ de: '2026-10-10', ate: '2026-10-10' });
    expect(utils.datasDoPeriodo('semana')).toEqual({ de: '2026-10-05', ate: '2026-10-11' });   // 09/10 é sexta
    expect(utils.datasDoPeriodo('proximos30')).toEqual({ de: '2026-10-09', ate: '2026-11-08' });
    expect(utils.tituloDoDia('2026-11-02')).toBe('Segunda, 02/11');
  });

  it('nome sugerido do PDF (D14), sem caracteres proibidos', () => {
    expect(utils.nomeArquivoTermo('OS-2026-000512', 'Cozinha / Gourmet')).toBe('Termo OS-2026-000512 - Cozinha Gourmet');
    expect(utils.nomeArquivoTermos('OS-2026-000512', '2026-11-03')).toBe('Termos OS-2026-000512 - 03-11-2026');
  });
});

describe('aba Entrega da OS', () => {
  it('topo, agendamentos e um cartão por ambiente (D2, D3)', async () => {
    await montarAba();
    expect(el('resumo-entrega')!.textContent).toBe('1 de 3 ambientes entregues · 1 pendência aberta');
    // Ontem (Closet) atrasado e editável; amanhã (com a Cozinha já entregue) vira histórico.
    expect(el('agendamento-2')!.querySelector('[data-testid="atrasado"]')).not.toBeNull();
    expect(el('editar-agendamento-2')).not.toBeNull();
    expect(el('editar-agendamento-1')).toBeNull();
    const cozinha = el('entrega-1')!;
    expect(cozinha.textContent).toContain('Com ressalvas');
    expect(cozinha.textContent).toContain('recebido por Ana (síndica)');
    expect(cozinha.querySelector('[data-testid="resumo-checklist"]')!.textContent).toBe('3 ok · 1 não ok');
    expect(cozinha.textContent).toContain('Corrigir registro');
    expect(el('entrega-2')!.textContent).toContain('Instalação 10/10 às 08:00 · Carlos, Davi');
    expect(el('entrega-2')!.textContent).toContain('Registrar entrega');
    expect(corpo()).not.toMatch(/R\$/);                                      // nenhum preço (D11)
  });

  it('07 — agendar com montador ocupado: salva e avisa quem e onde', async () => {
    await montarAba(fixtures.inicial);
    api.agendar.mockResolvedValue(entrega(fixtures.ocupado));
    await clicar('agendar');
    await clicar('ambiente-1');
    await clicar('montador-2');
    await clicar('confirmar-agendar');
    expect(api.agendar).toHaveBeenCalledWith('OS-2026-000001', {
      data: '2026-10-10', hora_inicio: null, ambiente_ids: [1], montadores: [2], observacao: null,
    });
    expect(toast.warning).toHaveBeenCalledWith('Carlos já tem instalação em 10/10 às 08:00 na OS-2026-000001 (Dona Marta).');
    expect(el('confirmar-agendar')).toBeNull();                              // o modal fechou: está salvo
  });

  it('agendar sem ambiente ou montador: erro no modal, nada é enviado', async () => {
    await montarAba(fixtures.inicial);
    await clicar('agendar');
    await clicar('confirmar-agendar');
    expect(el('erro-agendar')!.textContent).toBe('Escolha pelo menos um ambiente e um montador.');
    expect(api.agendar).not.toHaveBeenCalled();
  });

  it('09 — imprimir os termos do agendamento com 2 ambientes: 2 termos, o segundo em página nova', async () => {
    await montarAba();
    const titulo = document.title;
    await clicar('imprimir-termos-1');
    const termos = [...document.body.querySelectorAll('[data-testid="termo-entrega"]')];
    expect(termos.map((t) => t.querySelector('[data-testid="termo-ambiente"]')!.textContent)).toEqual(['Cozinha Gourmet', 'Sala']);
    expect(termos[0].classList.contains('termo-nova-pagina')).toBe(false);
    expect(termos[1].classList.contains('termo-nova-pagina')).toBe(true);
    expect(document.title).toBe('Termos OS-2026-000001 - 10-10-2026');   // o nome do PDF
    expect(imprimirComPagina).toHaveBeenCalledWith('A4', { folha: 'A4' });
    window.dispatchEvent(new Event('afterprint'));                     // o diálogo fechou: tudo volta
    await flushPromises();
    expect(document.title).toBe(titulo);
    expect(document.body.querySelectorAll('[data-testid="termo-entrega"]')).toHaveLength(0);
  });

  it('10 — o último ambiente entregue pergunta "Finalizar a OS agora?"', async () => {
    const w = await montarAba(fixtures.semFoto);                       // só falta o Closet
    api.registrar.mockResolvedValue(entrega(fixtures.ultimo));
    el('entrega-3')!.querySelector<HTMLButtonElement>('[data-testid="registrar"]')!.click();
    await flushPromises();
    await clicar('situacao-conforme');
    await clicar('confirmar-registro');
    expect(corpo()).toContain('Registrar sem a foto do termo assinado?');  // D6 primeiro
    botaoComTexto('Registrar sem a foto')!.click();
    await flushPromises();
    expect(api.registrar).toHaveBeenCalledTimes(1);
    expect(corpo()).toContain('Finalizar a OS agora?');
    botaoComTexto('Finalizar a OS')!.click();
    await flushPromises();
    expect(w.emitted('finalizar')).toHaveLength(1);
  });

  it('as fotos sobem ANTES do registro (o backend vê a foto do termo)', async () => {
    await montarAba(fixtures.inicial);
    const ordem: string[] = [];
    api.enviarFoto.mockImplementation(async (_os: string, _id: number, tipo: string) => { ordem.push(tipo); return entrega(fixtures.inicial); });
    api.registrar.mockImplementation(async () => { ordem.push('REGISTRO'); return entrega(fixtures.inicial); });
    el('entrega-2')!.querySelector<HTMLButtonElement>('[data-testid="registrar"]')!.click();
    await flushPromises();
    await clicar('situacao-conforme');
    const termo = el('foto-termo') as HTMLInputElement;
    Object.defineProperty(termo, 'files', { value: [new File(['x'], 'termo.png', { type: 'image/png' })] });
    termo.dispatchEvent(new Event('change'));
    await clicar('confirmar-registro');
    expect(corpo()).not.toContain('Registrar sem a foto do termo assinado?');   // com a foto, não pergunta
    expect(ordem).toEqual(['TERMO', 'REGISTRO']);
  });

  it('OS fechada: sem agendar nem registrar, mas "+ Pendência" continua (D10)', async () => {
    await montarAba(fixtures.fechada);
    expect(el('entrega-fechada')!.textContent).toContain('A OS está finalizada');
    expect(el('agendar')).toBeNull();
    expect(el('entrega-1')!.querySelector('[data-testid="registrar"]')).toBeNull();
    expect(el('entrega-1')!.querySelector('[data-testid="nova-pendencia"]')).not.toBeNull();
  });

  it('resolver a pendência aberta', async () => {
    await montarAba();
    api.resolverPendencia.mockResolvedValue(entrega());
    await clicar('resolver-1');
    const campo = el('resolucao') as HTMLTextAreaElement;
    campo.value = 'Porta ajustada';
    campo.dispatchEvent(new Event('input'));
    await flushPromises();
    await clicar('confirmar-resolver');
    expect(api.resolverPendencia).toHaveBeenCalledWith('OS-2026-000001', 1, 1, 'Porta ajustada', '2026-10-09');
  });
});

describe('RegistrarEntregaModal', () => {
  function montarModal(nome = 'Sala') {
    const w = mount(RegistrarEntregaModal, {
      props: { isOpen: true, entrega: ambiente(entrega(), nome), funcionarios: FUNCIONARIOS, gravando: false },
      attachTo: document.body,
    });
    montados.push(w);
    return w;
  }

  it('04 — com ressalvas sem pendência: erro no campo de pendências', async () => {
    const w = montarModal();
    await clicar('situacao-ressalvas');
    await clicar('confirmar-registro');
    expect(el('erro-pendencias')!.textContent).toBe('Com ressalvas, informe pelo menos uma pendência.');
    expect(w.emitted('confirmar')).toBeUndefined();
  });

  it('05 — sem a foto do termo: pergunta antes de enviar; "Cancelar" não envia', async () => {
    const w = montarModal();
    await clicar('situacao-conforme');
    await clicar('confirmar-registro');
    expect(corpo()).toContain('Registrar sem a foto do termo assinado?');
    botaoComTexto('Cancelar')!.click();                                // o "Cancelar" do diálogo (o último aberto)
    await flushPromises();
    expect(w.emitted('confirmar')).toBeUndefined();
  });

  it('06 — montadores já marcados com os do agendamento do ambiente', () => {
    montarModal('Sala');
    expect((el('registro-montador-2') as HTMLInputElement).checked).toBe(true);    // Carlos
    expect((el('registro-montador-3') as HTMLInputElement).checked).toBe(true);    // Davi
  });

  it('checklist em três estados e as pendências uma por linha', async () => {
    const w = montarModal('Cozinha Gourmet');                        // já tem foto do termo: não pergunta
    await clicar('situacao-ressalvas');
    await clicar('marcacao-4');                                      // em branco → ✓
    const pendencias = el('pendencias') as HTMLTextAreaElement;
    pendencias.value = 'Falta rodapé\n\n  Vidro trincado ';
    pendencias.dispatchEvent(new Event('input'));
    await flushPromises();
    await clicar('confirmar-registro');
    const [registro] = w.emitted('confirmar')![0] as [Record<string, unknown>];
    expect(registro.checklist).toEqual(['ok', 'ok', 'nao_ok', 'ok', 'ok']);
    expect(registro.pendencias).toEqual(['Falta rodapé', 'Vidro trincado']);
    expect(registro.montadores).toEqual([2, 3]);                     // os do registro de antes
  });
});

describe('TermoEntregaPrint', () => {
  it('08 — sem preço; checklist com OK e Não OK; 6 linhas; duas assinaturas', () => {
    const dados = entrega();
    const w = mount(TermoEntregaPrint, {
      props: { dados, entrega: ambiente(dados, 'Cozinha Gourmet') }, attachTo: document.body, global: { plugins: plugins() },
    });
    montados.push(w);
    const termo = el('termo-entrega')!;
    expect(termo.textContent).toContain('TERMO DE ENTREGA E INSTALAÇÃO');
    expect(termo.textContent).toContain('PRJ-2026-000001');
    expect(termo.textContent).toContain('Av. das Américas, 4200 — Apto 802');
    expect(termo.textContent).toContain('L 700 × A 2200 × P 600 mm');
    const cabecalho = [...termo.querySelectorAll('[data-testid="termo-checklist"] th')].map((th) => th.textContent?.trim());
    expect(cabecalho).toEqual(['Vistoria', 'OK', 'Não OK']);
    expect(termo.querySelectorAll('[data-testid="termo-linha"]')).toHaveLength(6);
    expect(termo.textContent).toContain('Cliente / recebedor (nome e doc.)');
    expect(termo.textContent).toContain('Montador');
    expect(termo.textContent).toContain('Recebi os móveis acima, instalados e em condições de uso');
    expect(termo.textContent).not.toMatch(/R\$|preço|valor/i);
    // Preto e branco: nenhuma classe de cor no papel (o check:print-bw também confere).
    expect(termo.outerHTML).not.toMatch(/(red|amber|emerald|blue|zinc|gray|slate)-\d/);
  });
});

describe('aviso da finalização (D18, D19)', () => {
  it('11 — pendência aberta e ambiente não entregue: bloco âmbar, só informativo', async () => {
    api.getResumo.mockResolvedValue(schemas.resumoSchema.parse(structuredClone(fixtures.resumo)));
    const w = mount(AvisoEntregaFinalizacao, { props: { numeroOs: 'OS-2026-000001' }, global: { plugins: plugins() } });
    montados.push(w);
    await flushPromises();
    expect(w.get('[data-testid="aviso-ambientes"]').text()).toBe('Ambientes ainda não entregues: Sala, Closet.');
    expect(w.get('[data-testid="aviso-pendencias"]').text()).toContain('Porta do aéreo 2 desalinhada (Cozinha Gourmet)');
    expect(w.emitted()).toEqual({});                                  // não emite nada: não trava o modal
  });

  it('tudo entregue e sem pendência: nada aparece', async () => {
    api.getResumo.mockResolvedValue({ entregues: 3, total: 3, todos_entregues: true, ambientes_pendentes: [], pendencias_abertas: [] });
    const w = mount(AvisoEntregaFinalizacao, { props: { numeroOs: 'OS-2026-000001' }, global: { plugins: plugins() } });
    montados.push(w);
    await flushPromises();
    expect(w.find('[data-testid="aviso-entrega"]').exists()).toBe(false);
  });

  it('12 — no OSFinalizarModal o bloco só existe com a capacidade, e é carregado sob demanda', () => {
    expect(fonteFinalizar).toContain('<AvisoEntregaFinalizacao v-if="temOrcamentoTecnico && osNumero"');
    expect(fonteFinalizar).toContain("import('@/modules/marcenaria/entrega/components/AvisoEntregaFinalizacao.vue')");
    expect(fonteFinalizar).not.toMatch(/import .*AvisoEntregaFinalizacao.* from/);   // sem import estático
  });
});

describe('aba Instalações em Serviços', () => {
  const itens = () => schemas.instalacoesSchema.parse(structuredClone(fixtures.instalacoes)).itens;

  async function montarInstalacoes() {
    api.getInstalacoes.mockImplementation(async (f: { de?: string | null; ate?: string | null }) =>
      itens().filter((i) => (!f.de || i.data >= f.de) && (!f.ate || i.data <= f.ate)));
    const w = mount(InstalacoesTab, { attachTo: document.body, global: { plugins: plugins() } });
    montados.push(w);
    await flushPromises();
    return w;
  }

  it('padrão "Esta semana", agrupado por dia', async () => {
    await montarInstalacoes();
    expect(api.getInstalacoes).toHaveBeenCalledWith({ de: '2026-10-05', ate: '2026-10-11', atrasadas: false });
    expect(el('dia-2026-10-08')!.textContent).toContain('Quinta, 08/10');
    expect(el('dia-2026-10-10')!.textContent).toContain('Sábado, 10/10');
  });

  it('13 — "Amanhã": só os agendamentos de amanhã, num dia só', async () => {
    await montarInstalacoes();
    await clicar('periodo-amanha');
    expect(api.getInstalacoes).toHaveBeenLastCalledWith({ de: '2026-10-10', ate: '2026-10-10', atrasadas: false });
    expect(document.body.querySelectorAll('[data-testid^="dia-"]')).toHaveLength(1);
    expect(el('dia-2026-10-10')!.querySelectorAll('[data-testid^="instalacao-"]')).toHaveLength(2);
  });

  it('montador filtra na tela; "Só atrasadas" pede todas as atrasadas', async () => {
    await montarInstalacoes();
    const select = el('filtro-montador') as HTMLSelectElement;
    expect([...select.options].map((o) => o.textContent)).toEqual(['Todos', 'Carlos', 'Davi']);
    select.value = '3';                                              // Davi
    select.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(document.body.querySelectorAll('[data-testid^="instalacao-"]')).toHaveLength(1);
    const caixa = el('so-atrasadas') as HTMLInputElement;
    caixa.checked = true;
    caixa.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(api.getInstalacoes).toHaveBeenLastCalledWith({ de: null, ate: null, atrasadas: true });
  });

  it('14 — clique na OS: abre a OS na aba Entrega', async () => {
    await montarInstalacoes();
    const primeiro = itens()[0];
    await clicar(`abrir-os-${primeiro.id}`);
    expect(abrirOS).toHaveBeenCalledWith('OS-2026-000001', { abaInicial: 'entrega' });
  });

  it('imprimir a lista do dia (D17)', async () => {
    await montarInstalacoes();
    await clicar('imprimir-dia-2026-10-10');
    const folha = el('lista-do-dia')!;
    expect(folha.textContent).toContain('INSTALAÇÕES DO DIA');
    expect(folha.textContent).toContain('Av. das Américas, 4200');
    expect(folha.querySelectorAll('section')).toHaveLength(2);
    expect(imprimirComPagina).toHaveBeenCalledWith('A4', { folha: 'A4' });
  });
});
