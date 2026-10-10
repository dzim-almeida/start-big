/**
 * Spec 14 (marcenaria) ⚠️ `shared/etiquetas` só com ACRÉSCIMOS (FB2) — casos
 * 03, 04 e 05: o layout do volume do móvel, os modelos prontos e a prova de
 * que os modelos de produto e de envio continuam os mesmos.
 */
import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';

import { CAMPOS_MOVEL, CAMPOS_PRODUTO, CAMPOS_VOLUME } from '../campos';
import { gerarMovel } from '../layoutEnvio';
import { problemasDaPagina, type PaginaEtiqueta } from '../modelo';
import { PRESETS, PRESETS_DANFE, PRESETS_MOVEL, PRESETS_VOLUME } from '../presets';
import { problemasDosElementos } from '../editor/operacoes';
import EtiquetaView from '../components/EtiquetaView.vue';

// A impressão direta (Tauri) não existe no teste; o motor decide pelo config.
vi.mock('@/shared/services/impressao.service', () => ({ impressaoDisponivel: () => true }));
const { motivoParaDriver } = await import('../nativo/imprimirNativo');

const pagina = (largura: number, altura: number): PaginaEtiqueta => ({
  tipo: 'bobina', largura_mm: largura, altura_mm: altura, colunas: 1, espaco_colunas_mm: 0,
  espaco_linhas_mm: 0, margem_esq_mm: 0, margem_topo_mm: 0, folha: null,
});
/** Os campos que um layout desenha. */
const campos = (p: PaginaEtiqueta) =>
  gerarMovel(p).flatMap((e) => ('campo' in e && e.campo ? [e.campo] : []));

describe('layout do volume do móvel (D3)', () => {
  it('03 — 105 × 148,5 (A4 em 4): versão completa, tudo dentro da página', () => {
    const p = { ...pagina(105, 148.5) };
    expect(problemasDosElementos(gerarMovel(p), p)).toEqual([]);
    expect(campos(p)).toEqual([
      'projeto.codigo', 'os.numero', 'movel.nome', 'movel.ambiente', 'movel.medidas', 'volume.rotulo',
      'cliente.nome', 'projeto.endereco_obra', 'empresa.nome',
    ]);
  });

  it('03 — 100 × 50 (térmica): versão compacta, sem a empresa, endereço numa linha', () => {
    const p = pagina(100, 50);
    expect(problemasDosElementos(gerarMovel(p), p)).toEqual([]);
    expect(campos(p)).not.toContain('empresa.nome');
    const endereco = gerarMovel(p).find((e) => 'campo' in e && e.campo === 'projeto.endereco_obra');
    expect(endereco && 'linhas_max' in endereco ? endereco.linhas_max : null).toBe(1);
  });

  it('o "VOLUME 2 DE 5" sai em negrito e centralizado; nenhum campo de preço', () => {
    const volume = gerarMovel(pagina(100, 150)).find((e) => 'campo' in e && e.campo === 'volume.rotulo');
    expect(volume).toMatchObject({ negrito: true, alinhamento: 'centro' });
    expect(CAMPOS_MOVEL.map((c) => c.campo).filter((c) => c.startsWith('preco'))).toEqual([]);
  });
});

describe('modelos prontos (D4)', () => {
  it('04 — os modelos de produto e de envio são os mesmos de antes', () => {
    expect(PRESETS.map((p) => p.chave)).toEqual([
      'preset:rolo-40x25', 'preset:rolo-50x30', 'preset:rolo-60x40', 'preset:rolo-33x22-3col', 'preset:gondola-100x30',
      'preset:pimaco-6180', 'preset:pimaco-6181', 'preset:pimaco-6182', 'preset:pimaco-6183',
      'preset:a4-65-38x21', 'preset:a4-21-63x38', 'preset:a4-14-99x38',
    ]);
    expect(PRESETS_VOLUME.map((p) => p.chave)).toEqual([
      'preset:volume-100x150', 'preset:volume-100x100', 'preset:volume-100x50', 'preset:volume-a4-4',
    ]);
    expect(PRESETS_DANFE.map((p) => p.chave)).toEqual(['preset:danfe-100x150', 'preset:danfe-a4-4']);
    // Os campos novos não entram nas listas de produto e de envio.
    const novos = CAMPOS_MOVEL.map((c) => c.campo).filter((c) => !['volume.contador', 'volume.rotulo', 'empresa.nome'].includes(c));
    expect([...CAMPOS_PRODUTO, ...CAMPOS_VOLUME].map((c) => c.campo).filter((c) => novos.includes(c))).toEqual([]);
  });

  it('05 — PRESETS_MOVEL: 3 modelos de volume, chaves "preset:movel-*", todos cabem no papel', () => {
    expect(PRESETS_MOVEL.map((p) => [p.chave, p.fonte])).toEqual([
      ['preset:movel-a4-4', 'volume'], ['preset:movel-100x150', 'volume'], ['preset:movel-100x50', 'volume'],
    ]);
    for (const modelo of PRESETS_MOVEL) {
      expect(problemasDaPagina(modelo.definicao.pagina)).toEqual([]);
      expect(problemasDosElementos(modelo.definicao.elementos, modelo.definicao.pagina)).toEqual([]);
    }
    expect(PRESETS_MOVEL[0].definicao.pagina.tipo).toBe('folha');      // o padrão: impressora comum
  });

  it('07 — térmica com impressão direta: o motor vai pelo nativo; a folha A4 vai pelo driver', () => {
    const direta = { etiqueta_saida: 'direta' } as never;
    expect(motivoParaDriver(direta, PRESETS_MOVEL[2].definicao)).toBeNull();
    expect(motivoParaDriver(direta, PRESETS_MOVEL[0].definicao)).toBe('folha é papel de impressora comum');
  });

  it('a etiqueta desenhada mostra o volume, o projeto e o móvel', () => {
    const w = mount(EtiquetaView, {
      props: {
        definicao: PRESETS_MOVEL[1].definicao,
        valores: {
          'projeto.codigo': 'PRJ-000031', 'os.numero': 'OS-2026-000512', 'movel.nome': 'Guarda-roupa casal',
          'movel.ambiente': 'Dormitório casal', 'volume.rotulo': 'VOLUME 2 DE 5', 'cliente.nome': 'Maria Souza',
        },
      },
    });
    for (const texto of ['PRJ-000031', 'OS-2026-000512', 'Guarda-roupa casal', 'VOLUME 2 DE 5', 'Maria Souza']) {
      expect(w.text()).toContain(texto);
    }
  });
});
