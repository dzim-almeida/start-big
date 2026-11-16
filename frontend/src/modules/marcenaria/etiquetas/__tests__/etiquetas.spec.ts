/**
 * Spec 14 §10 — as etiquetas por volume do móvel (casos 01, 02, 06, 08, 09;
 * os casos 03-05 e 07 do motor estão em shared/etiquetas/__tests__/movel.spec.ts).
 *
 * Os móveis vêm da resposta REAL da produção (fixtures da 12B).
 */
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { createPinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowRef } from 'vue';

// O motor de impressão é simulado: aqui só importa O QUE o modal manda imprimir.
const imprimir = vi.fn();
const trabalho = shallowRef(null);
vi.mock('@/shared/etiquetas/useImpressaoEtiquetas', () => ({ useImpressaoEtiquetas: () => ({ trabalho, imprimir }) }));

const { default: ImprimirEtiquetasModal } = await import('../components/ImprimirEtiquetasModal.vue');
const { montarEtiquetas, valoresDoVolumeDoMovel, resumoDaImpressao } = await import('../utils/montarEtiquetas');
const { PRESETS_MOVEL } = await import('@/shared/etiquetas/presets');
const { paginar } = await import('@/shared/etiquetas/paginacao');
const { producaoSchema } = await import('@/modules/marcenaria/producao/schemas/producao.schema');
const { novoQueryClient } = await import('@/modules/marcenaria/orcamentos/__tests__/apoio');
const fixtura = (await import('@/modules/marcenaria/producao/__tests__/fixtures/producao.json')).default;

const COMUM = { os: 'OS-2026-000512', projeto: 'PRJ-000031', enderecoObra: 'Av. das Américas, 4200', cliente: 'Maria Souza', empresa: 'Marcenaria Exemplo' };
const aereo = { nome: 'Armário aéreo', ambiente: 'Cozinha Gourmet', medidas: { largura_mm: 800, altura_mm: 700, profundidade_mm: 350 } };
const guardaRoupa = { nome: 'Guarda-roupa casal', ambiente: 'Dormitório casal', medidas: { largura_mm: 2400, altura_mm: 2600, profundidade_mm: 600 } };

describe('valores das etiquetas (§5)', () => {
  it('01 — aéreo × 3 e guarda-roupa × 5: 8 etiquetas, na ordem móvel → volume', () => {
    const etiquetas = montarEtiquetas([{ movel: aereo, volumes: 3 }, { movel: guardaRoupa, volumes: 5 }], COMUM);
    expect(etiquetas.map((e) => e['volume.rotulo'])).toEqual([
      'VOLUME 1 DE 3', 'VOLUME 2 DE 3', 'VOLUME 3 DE 3',
      'VOLUME 1 DE 5', 'VOLUME 2 DE 5', 'VOLUME 3 DE 5', 'VOLUME 4 DE 5', 'VOLUME 5 DE 5',
    ]);
    expect(etiquetas[4]).toMatchObject({ 'movel.nome': 'Guarda-roupa casal', 'volume.contador': '2/5' });
  });

  it('02 — nenhuma chave de preço; medidas no formato da proposta', () => {
    const valores = valoresDoVolumeDoMovel(aereo, 1, 3, COMUM);
    expect(Object.keys(valores).filter((k) => /preco|valor|custo/.test(k))).toEqual([]);
    expect(valores['movel.medidas']).toBe('L 800 × A 700 × P 350 mm');
    expect(valores).toMatchObject({ 'os.numero': 'OS-2026-000512', 'projeto.codigo': 'PRJ-000031', 'cliente.nome': 'Maria Souza' });
  });

  it('06 — folha A4 em 4, começar na 3, 8 etiquetas: pula 2 e usa 3 folhas', () => {
    const pagina = PRESETS_MOVEL[0].definicao.pagina;
    expect(resumoDaImpressao(pagina, 8, 2)).toBe('8 etiquetas · 3 folhas');
    expect(paginar(pagina, Array.from({ length: 8 }), 2)).toHaveLength(3);
    expect(resumoDaImpressao(PRESETS_MOVEL[2].definicao.pagina, 8, 2)).toBe('8 etiquetas');   // rolo: sem folha
  });
});

describe('modal "Imprimir etiquetas"', () => {
  const producao = producaoSchema.parse(structuredClone(fixtura));
  const montados: ReturnType<typeof mount>[] = [];
  const el = (testid: string) => document.body.querySelector(`[data-testid="${testid}"]`) as HTMLElement | null;

  function montar(marcados: number[]) {
    const w = mount(ImprimirEtiquetasModal, {
      props: {
        isOpen: true, numeroOs: 'OS-2026-000001', moveis: producao.moveis, marcados,
        obra: { projeto: 'PRJ-2026-000001', enderecoObra: 'Av. das Américas, 4200', cliente: 'Dona Marta' },
      },
      attachTo: document.body,
      global: { plugins: [[VueQueryPlugin, { queryClient: novoQueryClient() }], createPinia()] as never },
    });
    montados.push(w);
    return w;
  }

  beforeEach(() => { imprimir.mockReset(); window.localStorage.clear(); });
  afterEach(() => { montados.splice(0).forEach((w) => w.unmount()); document.body.innerHTML = ''; });

  it('volumes começam na quantidade; começar na 3 → pular 2; calibração do terminal; título do PDF', async () => {
    montar([1, 2]);
    expect((el('volumes-1') as HTMLInputElement).value).toBe('1');
    const volumes = el('volumes-1') as HTMLInputElement;
    volumes.value = '5';
    volumes.dispatchEvent(new Event('change'));
    const comecar = el('comecar-em') as HTMLInputElement;
    comecar.value = '3';
    comecar.dispatchEvent(new Event('input'));
    await flushPromises();
    expect(el('resumo-etiquetas')!.textContent).toBe('6 etiquetas · 2 folhas');
    el('imprimir-etiquetas')!.click();
    await flushPromises();
    const [job] = imprimir.mock.calls[0];
    expect(job.pular).toBe(2);
    expect(job.etiquetas.map((e: Record<string, string>) => e['volume.rotulo'])).toEqual([
      'VOLUME 1 DE 5', 'VOLUME 2 DE 5', 'VOLUME 3 DE 5', 'VOLUME 4 DE 5', 'VOLUME 5 DE 5', 'VOLUME 1 DE 1',
    ]);
    expect(job.etiquetas[0]).toMatchObject({ 'projeto.codigo': 'PRJ-2026-000001', 'cliente.nome': 'Dona Marta', 'movel.nome': 'Balcão' });
    expect([job.deslocamentoX, job.deslocamentoY]).toEqual([0, 0]);
    expect(job.definicao).toBe(PRESETS_MOVEL[0].definicao);
  });

  it('09 — o móvel terceirizado também pode ser marcado', () => {
    montar([]);
    expect(el('etiqueta-movel-4')).not.toBeNull();                 // Torre Quente (terceirizada)
    expect((el('imprimir-etiquetas') as HTMLButtonElement).disabled).toBe(true);   // nada marcado
  });

  it('D11 — o modelo escolhido fica lembrado; sem armazenamento, volta ao A4 em 4', async () => {
    montar([1]);
    const select = el('modelo-etiqueta') as HTMLSelectElement;
    select.value = 'preset:movel-100x50';
    select.dispatchEvent(new Event('change'));
    await flushPromises();
    expect(el('comecar-em')).toBeNull();                           // rolo: sem "começar na posição"
    el('imprimir-etiquetas')!.click();
    await flushPromises();
    montados.splice(0).forEach((w) => w.unmount());
    montar([1]);
    expect((el('modelo-etiqueta') as HTMLSelectElement).value).toBe('preset:movel-100x50');

    montados.splice(0).forEach((w) => w.unmount());
    // Bloqueia só a chave da marcenaria (o store da impressora também lê o armazenamento).
    const original = Storage.prototype.getItem;
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(function (this: Storage, chave: string) {
      if (chave.startsWith('startbig.marcenaria')) throw new Error('bloqueado');
      return original.call(this, chave);
    });
    montar([1]);
    expect((el('modelo-etiqueta') as HTMLSelectElement).value).toBe('preset:movel-a4-4');
    vi.restoreAllMocks();
  });
});
