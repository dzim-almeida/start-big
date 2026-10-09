/**
 * Spec 12B §11 — a aba Produção da OS e o quadro da fábrica (casos 03-14;
 * os casos 01-02 das abas estão em OSFormAbasOrcamento.spec.ts e
 * OrdemServicoView.abas.spec.ts).
 *
 * Os JSON de `fixtures/` são respostas REAIS da API da 12A, gerados por um
 * teste temporário do backend em 09/10/2026: OS com Balcão (Corte e Borda
 * concluídas, Furação em execução), Aéreo (Corte concluída), Armário (tudo
 * pendente) e a Torre Quente terceirizada a caminho. O relógio dos testes
 * fica em 09/10/2026, o dia em que as fixtures nasceram.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

// --- API simulada ----------------------------------------------------------------
const api = {
  getProducao: vi.fn(),
  concluir: vi.fn(),
  iniciar: vi.fn(),
  reabrir: vi.fn(),
  editarEtapas: vi.fn(),
  aplicarPadrao: vi.fn(),
  getQuadro: vi.fn(),
};
vi.mock('../services/producao.service', () => ({
  getProducao: (...a: unknown[]) => api.getProducao(...a),
  concluir: (...a: unknown[]) => api.concluir(...a),
  iniciar: (...a: unknown[]) => api.iniciar(...a),
  reabrir: (...a: unknown[]) => api.reabrir(...a),
  editarEtapas: (...a: unknown[]) => api.editarEtapas(...a),
  aplicarPadrao: (...a: unknown[]) => api.aplicarPadrao(...a),
  getQuadro: (...a: unknown[]) => api.getQuadro(...a),
}));
const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() };
vi.mock('@/shared/composables/useToast', () => ({ useToast: () => toast }));
vi.mock('@/modules/order-service/shared/segmento/useRotulosStatusOS', () => ({
  useRotulosStatusOS: () => ({ rotuloStatus: (s: string) => ({ FINALIZADA: 'Finalizada', CANCELADA: 'Cancelada' }[s] ?? s) }),
}));
// O usuário logado é o funcionário 1 ("Admin Master" nas fixtures).
vi.mock('@/shared/stores/auth.store', () => ({ useAuthStore: () => ({ userData: { funcionario_id: 1 } }) }));
const abrirOS = vi.fn();
vi.mock('@/modules/marcenaria/orcamentos/composables/useAbrirOS', () => ({
  useAbrirOS: () => ({ abrirOS, abrindo: ref(false) }),
}));

const { default: OSProducaoTab } = await import('../components/OSProducaoTab.vue');
const { default: QuadroProducaoTab } = await import('../components/QuadroProducaoTab.vue');
const { default: SugestaoStatusModal } = await import('../components/SugestaoStatusModal.vue');
const schemas = await import('../schemas/producao.schema');
const utils = await import('../utils/producao');
const { limparFeitoPor } = await import('../composables/useFeitoPor');
const { novoQueryClient } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');
const fixtures = {
  producao: (await import('./fixtures/producao.json')).default,
  inicial: (await import('./fixtures/producao-inicial.json')).default,
  semEtapas: (await import('./fixtures/producao-sem-etapas.json')).default,
  fechada: (await import('./fixtures/producao-fechada.json')).default,
  emProducao: (await import('./fixtures/concluir-sugestao-em-producao.json')).default,
  aguardando: (await import('./fixtures/concluir-sugestao-aguardando.json')).default,
  quadro: (await import('./fixtures/quadro.json')).default,
};

type Producao = ReturnType<typeof schemas.producaoSchema.parse>;
/** Uma cópia nova (e conferida pelo zod) da resposta real. */
const producao = (dados: unknown = fixtures.producao): Producao => schemas.producaoSchema.parse(structuredClone(dados));
const plugins = () => [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never;
const FUNCIONARIOS = [{ id: 1, nome: 'Admin Master' }, { id: 7, nome: 'Pedro' }];

/** Uma promessa que o teste resolve na hora que quiser (para ver a tela otimista). */
function adiada<T>() {
  let resolver!: (valor: T) => void;
  let rejeitar!: (erro: unknown) => void;
  const promessa = new Promise<T>((res, rej) => { resolver = res; rejeitar = rej; });
  return { promessa, resolver, rejeitar };
}

const montados: ReturnType<typeof mount>[] = [];
const aplicarStatus = vi.fn();
async function montarAba(dados: unknown = fixtures.producao) {
  api.getProducao.mockResolvedValue(producao(dados));
  const w = mount(OSProducaoTab, {
    props: { numeroOs: 'OS-2026-000001', funcionarios: FUNCIONARIOS, aplicarStatus },
    attachTo: document.body,
    global: { plugins: plugins() },
  });
  montados.push(w);
  await flushPromises();
  return w;
}
const corpo = () => document.body.textContent ?? '';
const el = (testid: string) => document.body.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;
const statusDoChip = (id: number) => el(`chip-${id}`)?.getAttribute('data-status');
async function clicar(testid: string) {
  el(testid)!.click();
  await flushPromises();
}
/** O botão do modal de confirmação pelo texto. */
const botaoComTexto = (texto: string) =>
  [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === texto) as HTMLButtonElement | undefined;

beforeEach(() => {
  for (const f of [...Object.values(api), ...Object.values(toast), abrirOS, aplicarStatus]) f.mockReset();
  limparFeitoPor();
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date(2026, 9, 9, 10, 0));          // 09/10/2026, o dia em que as fixtures nasceram
});
afterEach(() => {
  montados.splice(0).forEach((w) => w.unmount());
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('respostas reais da 12A', () => {
  it('produção (todos os momentos) e quadro passam no zod', () => {
    for (const dados of [fixtures.producao, fixtures.inicial, fixtures.semEtapas, fixtures.fechada, fixtures.emProducao, fixtures.aguardando]) {
      schemas.producaoSchema.parse(dados);
    }
    expect(schemas.producaoSchema.parse(fixtures.emProducao).sugestao_status?.rotulo).toBe('Em Produção');
    expect(schemas.quadroSchema.parse(fixtures.quadro).itens).toHaveLength(2);
  });
});

describe('regras de tela', () => {
  it('"Concluir em todos": um botão por etapa com pendência, na ordem, com quantos faltam', () => {
    const lote = utils.etapasParaConcluirEmTodos(producao().moveis);
    expect(lote.map((g) => [g.nome, g.etapaIds])).toEqual([
      ['Corte', [11]], ['Borda', [7, 12]], ['Furação', [3, 8, 13]], ['Montagem', [4, 9, 14]], ['Embalagem', [5, 10, 15]],
    ]);
  });

  it('prazo da entrega: faltam, é hoje, atrasada', () => {
    expect(utils.prazoDaEntrega('2026-11-08')).toEqual({ texto: 'faltam 30 dias', atrasada: false });
    expect(utils.prazoDaEntrega('2026-10-09')).toEqual({ texto: 'é hoje', atrasada: false });
    expect(utils.prazoDaEntrega('2026-10-04')).toEqual({ texto: '5 dias atrasada', atrasada: true });
  });

  it('marcação otimista: muda as etapas e refaz o progresso, sem mexer no original', () => {
    const antes = producao();
    const depois = utils.marcarLocalmente(antes, [11, 12, 13, 14, 15], 'CONCLUIDA', 'Pedro');
    const armario = depois.moveis.find((m) => m.nome === 'Armário')!;
    expect(armario.pronto).toBe(true);
    expect(armario.proxima_etapa).toBeNull();
    expect(depois.progresso).toMatchObject({ etapas_concluidas: 8, moveis_prontos: 1 });
    expect(antes.progresso.etapas_concluidas).toBe(3);                     // a cópia é nova
  });
});

describe('aba Produção da OS', () => {
  it('topo: progresso, previsão e "Concluir em todos" (D2); terceirizado com a situação (D7)', async () => {
    await montarAba();
    expect(el('progresso')!.textContent).toMatch(/3 de 15 etapas ·\s*0 de 4 móveis prontos/);
    expect(el('previsao-entrega')!.textContent).toContain('Entrega prevista 08/11 · faltam 30 dias');
    expect(el('lote-Corte')!.textContent).toContain('Corte (1)');
    expect(el('lote-Borda')!.textContent).toContain('Borda (2)');
    expect(el('situacao-terceirizado')!.textContent).toContain('Pedido enviado · chega 20/10');
    // Em execução mostra quem está fazendo (D3).
    expect(el('chip-3')!.textContent).toContain('Furação');
    expect(el('chip-3')!.textContent).toContain('Admin Master');
    expect(corpo()).not.toMatch(/R\$/);                                      // nenhum preço (P4)
  });

  it('03 — clique no chip da próxima etapa: conclui sem confirmação', async () => {
    await montarAba();
    api.concluir.mockResolvedValue(producao());
    await clicar('chip-7');                                                  // Aéreo: Borda é a próxima
    expect(corpo()).not.toContain('antes de');
    expect(api.concluir).toHaveBeenCalledWith('OS-2026-000001', [7], 1);    // o usuário logado
  });

  it('04 — chip que não é o próximo: "Concluir Montagem antes de Borda?"', async () => {
    await montarAba();
    api.concluir.mockResolvedValue(producao());
    await clicar('chip-9');                                                  // Aéreo: Montagem
    expect(corpo()).toContain('Concluir Montagem antes de Borda?');
    expect(api.concluir).not.toHaveBeenCalled();
    botaoComTexto('Concluir')!.click();
    await flushPromises();
    expect(api.concluir).toHaveBeenCalledWith('OS-2026-000001', [9], 1);
  });

  it('05 — "Concluir em todos: Borda (2)": um POST e os 2 chips verdes na hora (D11)', async () => {
    await montarAba();
    const resposta = adiada<Producao>();
    api.concluir.mockReturnValue(resposta.promessa);
    await clicar('lote-Borda');
    expect(api.concluir).toHaveBeenCalledTimes(1);
    expect(api.concluir).toHaveBeenCalledWith('OS-2026-000001', [7, 12], 1);
    // Antes da resposta, a tela já mostra concluído (otimista).
    expect([statusDoChip(7), statusDoChip(12)]).toEqual(['CONCLUIDA', 'CONCLUIDA']);
    expect(el('progresso')!.textContent).toContain('5 de 15 etapas');
    resposta.resolver(utils.marcarLocalmente(producao(), [7, 12], 'CONCLUIDA'));
    await flushPromises();
    expect([statusDoChip(7), statusDoChip(12)]).toEqual(['CONCLUIDA', 'CONCLUIDA']);
  });

  it('06 — falha de rede ao concluir: o chip volta e o toast avisa', async () => {
    await montarAba();
    // A releitura depois do erro fica pendente: quem volta o chip é o "desfazer", não ela.
    api.getProducao.mockReturnValue(new Promise(() => {}));
    const resposta = adiada<Producao>();
    api.concluir.mockReturnValue(resposta.promessa);
    await clicar('chip-7');
    expect(statusDoChip(7)).toBe('CONCLUIDA');                               // otimista
    resposta.rejeitar(new Error('rede'));
    await flushPromises();
    expect(statusDoChip(7)).toBe('PENDENTE');                                // voltou
    expect(toast.error).toHaveBeenCalledWith('Não foi possível marcar a etapa.', expect.any(String));
  });

  it('07 — resposta com sugestão: "A produção começou. Mover a OS para Em Produção?"', async () => {
    await montarAba(fixtures.inicial);
    api.concluir.mockResolvedValue(producao(fixtures.emProducao));
    aplicarStatus.mockResolvedValue(undefined);
    await clicar('chip-1');
    expect(el('pergunta-status')!.textContent).toContain('A produção começou. Mover a OS para Em Produção?');
    await clicar('mover-status');
    expect(aplicarStatus).toHaveBeenCalledWith('EM_ANDAMENTO');
    expect(toast.success).toHaveBeenCalledWith('OS movida para Em Produção.');
    expect(el('pergunta-status')).toBeNull();
  });

  it('07b — "Agora não": nada muda e a pergunta some (D14)', async () => {
    await montarAba(fixtures.inicial);
    api.concluir.mockResolvedValue(producao(fixtures.emProducao));
    await clicar('chip-1');
    await clicar('agora-nao');
    expect(aplicarStatus).not.toHaveBeenCalled();
    expect(el('pergunta-status')).toBeNull();
  });

  it('09 — "Feito por" = Pedro: a requisição vai com o Pedro (D6)', async () => {
    await montarAba();
    api.concluir.mockResolvedValue(producao());
    const select = el('feito-por') as HTMLSelectElement;
    select.value = '7';
    select.dispatchEvent(new Event('change'));
    await flushPromises();
    await clicar('chip-7');
    expect(api.concluir).toHaveBeenCalledWith('OS-2026-000001', [7], 7);
  });

  it('10 — móvel sem etapas: aviso e "Aplicar etapas padrão"', async () => {
    await montarAba(fixtures.semEtapas);
    api.aplicarPadrao.mockResolvedValue(producao(fixtures.semEtapas));
    expect(el('sem-etapas')!.textContent).toContain('Este móvel não tem etapas de produção.');
    await clicar('aplicar-padrao');
    const nicho = producao(fixtures.semEtapas).moveis.find((m) => m.nome === 'Nicho')!;
    expect(api.aplicarPadrao).toHaveBeenCalledWith('OS-2026-000001', nicho.movel_id);   // o número vem da prop
  });

  it('11 — editar etapas: a concluída não é removida nem renomeada; a nova vai sem id', async () => {
    await montarAba();
    api.editarEtapas.mockResolvedValue(producao());
    await clicar('menu-movel-1');
    await clicar('opcao-editar-etapas');
    const corte = document.body.querySelector('input[aria-label="etapa 1"]') as HTMLInputElement;
    expect(corte.readOnly).toBe(true);                                       // Corte está concluída
    expect(corte.title).toBe('Etapa concluída: reabra antes de remover ou renomear.');
    const removerCorte = document.body.querySelector('button[aria-label="Remover etapa Corte"]') as HTMLButtonElement;
    expect(removerCorte.disabled).toBe(true);
    const removerMontagem = document.body.querySelector('button[aria-label="Remover etapa Montagem"]') as HTMLButtonElement;
    expect(removerMontagem.disabled).toBe(false);                            // pendente: pode

    botaoComTexto('Adicionar etapa')!.click();
    await flushPromises();
    const nova = document.body.querySelector('input[aria-label="etapa 6"]') as HTMLInputElement;
    nova.value = 'Pintura';
    nova.dispatchEvent(new Event('input'));
    await flushPromises();
    await clicar('salvar-etapas');
    expect(api.editarEtapas).toHaveBeenCalledWith('OS-2026-000001', 1, [
      { id: 1, nome: 'Corte' }, { id: 2, nome: 'Borda' }, { id: 3, nome: 'Furação' },
      { id: 4, nome: 'Montagem' }, { id: 5, nome: 'Embalagem' }, { id: null, nome: 'Pintura' },
    ]);
  });

  it('modo seleção: marca chips de vários móveis e conclui num POST só (D5)', async () => {
    await montarAba();
    api.concluir.mockResolvedValue(producao());
    await clicar('modo-selecao');
    await clicar('chip-8');                                                  // Aéreo: Furação
    await clicar('chip-13');                                                 // Armário: Furação
    expect(api.concluir).not.toHaveBeenCalled();                             // marcar não conclui
    expect(el('barra-selecao')!.textContent).toContain('2 etapas marcadas');
    await clicar('concluir-selecionadas');
    expect(api.concluir).toHaveBeenCalledWith('OS-2026-000001', [8, 13], 1);
  });

  it('iniciar pelo menu do chip, escolhendo quem vai fazer (D4)', async () => {
    await montarAba();
    api.iniciar.mockResolvedValue(producao());
    el('chip-12')!.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true }));
    await flushPromises();
    await clicar('opcao-iniciar');
    const select = el('responsavel-iniciar') as HTMLSelectElement;
    expect(select.value).toBe('1');                                          // vem com o "Feito por"
    select.value = '7';
    select.dispatchEvent(new Event('change'));
    await clicar('confirmar-iniciar');
    expect(api.iniciar).toHaveBeenCalledWith('OS-2026-000001', [12], 7);
  });

  it('clique no chip concluído: menu com "Reabrir"', async () => {
    await montarAba();
    api.reabrir.mockResolvedValue(producao());
    await clicar('chip-1');
    expect(api.concluir).not.toHaveBeenCalled();
    await clicar('opcao-reabrir');
    expect(api.reabrir).toHaveBeenCalledWith('OS-2026-000001', 1);
  });

  it('"Esconder móveis prontos" (D9)', async () => {
    await montarAba(fixtures.aguardando);
    expect(el('movel-1')).not.toBeNull();
    const caixa = el('esconder-prontos') as HTMLInputElement;
    caixa.checked = true;
    caixa.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(el('movel-1')).toBeNull();
    expect(el('prontos-escondidos')!.textContent).toContain('4 móveis prontos escondidos');
  });

  it('OS fechada: só leitura, com a frase (D10)', async () => {
    await montarAba(fixtures.fechada);
    expect(el('producao-fechada')!.textContent).toContain('A OS está finalizada: a produção não pode mais ser alterada.');
    expect(el('concluir-em-todos')).toBeNull();
    await clicar('chip-7');
    expect(api.concluir).not.toHaveBeenCalled();
  });

  it('sem `aplicarStatus` (fora do modal de OS), a pergunta não aparece', async () => {
    api.getProducao.mockResolvedValue(producao(fixtures.inicial));
    api.concluir.mockResolvedValue(producao(fixtures.emProducao));
    const w = mount(OSProducaoTab, { props: { numeroOs: 'OS-2026-000001' }, attachTo: document.body, global: { plugins: plugins() } });
    montados.push(w);
    await flushPromises();
    await clicar('chip-1');
    expect(el('pergunta-status')).toBeNull();
  });
});

describe('SugestaoStatusModal', () => {
  it('produção terminada: "Todos os móveis estão prontos. Mover a OS para Aguardando Entrega?"', () => {
    const sugestao = producao(fixtures.aguardando).sugestao_status;
    const w = mount(SugestaoStatusModal, { props: { sugestao, aplicando: false }, attachTo: document.body });
    montados.push(w);
    expect(el('pergunta-status')!.textContent).toContain('Todos os móveis estão prontos. Mover a OS para Aguardando Entrega?');
  });
});

describe('quadro da fábrica (Serviços › Produção)', () => {
  async function montarQuadro() {
    api.getQuadro.mockResolvedValue(schemas.quadroSchema.parse(structuredClone(fixtures.quadro)).itens);
    const w = mount(QuadroProducaoTab, { attachTo: document.body, global: { plugins: plugins() } });
    montados.push(w);
    await flushPromises();
    return w;
  }
  const linhas = () => [...document.body.querySelectorAll('tbody tr')].map((tr) => tr.getAttribute('data-testid'));

  it('12 — na ordem da previsão, a mais próxima primeiro; atraso em vermelho', async () => {
    await montarQuadro();
    expect(linhas()).toEqual(['linha-OS-2026-000003', 'linha-OS-2026-000002']);
    const primeira = el('linha-OS-2026-000003')!;
    expect(primeira.textContent).toContain('Em Produção');
    expect(primeira.textContent).toContain('0 de 3');
    expect(primeira.textContent).toContain('Furação (2)');
    expect(primeira.querySelector('[data-testid="entrega"]')!.textContent).toContain('04/10 (5 dias atrasada)');
    expect(el('linha-OS-2026-000002')!.querySelector('[data-testid="entrega"]')!.textContent).toContain('21/10 (12 dias)');
  });

  it('13 — clique na OS: abre o modal na aba Produção', async () => {
    await montarQuadro();
    await clicar('abrir-OS-2026-000003');
    expect(abrirOS).toHaveBeenCalledWith('OS-2026-000003', { abaInicial: 'producao' });
  });

  it('filtros: "Só atrasadas", status e busca (D17)', async () => {
    await montarQuadro();
    const atrasadas = el('so-atrasadas') as HTMLInputElement;
    atrasadas.checked = true;
    atrasadas.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(linhas()).toEqual(['linha-OS-2026-000003']);
    atrasadas.checked = false;
    atrasadas.dispatchEvent(new Event('change'));
    const status = el('filtro-status') as HTMLSelectElement;
    status.value = 'ABERTA';
    status.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(linhas()).toEqual(['linha-OS-2026-000002']);
    status.value = '';
    status.dispatchEvent(new Event('change'));
    const busca = el('busca-quadro') as HTMLInputElement;
    busca.value = '000003';
    busca.dispatchEvent(new Event('input'));
    await flushPromises();
    expect(linhas()).toEqual(['linha-OS-2026-000003']);
  });
});
