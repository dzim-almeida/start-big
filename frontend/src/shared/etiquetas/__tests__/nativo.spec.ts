import { describe, expect, it } from 'vitest';

import { bitmapVazio, deRgba, pintar } from '../nativo/bitmap';
import { comprimirLinhaZpl, gerarEpl, gerarTspl, gerarZpl, graficoZpl, type ConfigNativa } from '../nativo/linguagens';
import { agruparPaginas } from '../nativo/imprimirNativo';
import { quebrarTexto } from '../nativo/rasterizar';

const cfg: ConfigNativa = { dpi: 203, larguraMm: 50, alturaMm: 30, gapMm: 2, escuridao: null, girar180: false, inverter: false };
const texto = (bytes: Uint8Array) => new TextDecoder('latin1').decode(bytes);

/** 16 × 2 pontos: primeira linha com os 8 pontos da esquerda pretos. */
function bitmapTeste() {
  const b = bitmapVazio(16, 2);
  for (let x = 0; x < 8; x++) pintar(b, x, 0);
  return b;
}

describe('bitmap', () => {
  it('empacota 8 pontos por byte, o da esquerda no bit mais alto', () => {
    const b = bitmapVazio(10, 1);
    pintar(b, 0, 0);
    pintar(b, 9, 0);
    expect(b.bytesPorLinha).toBe(2);
    expect([...b.dados]).toEqual([0x80, 0x40]);
  });

  it('RGBA: escuro vira ponto, claro e transparente não', () => {
    const rgba = new Uint8ClampedArray([0, 0, 0, 255, 255, 255, 255, 255, 0, 0, 0, 0]);
    expect([...deRgba(rgba, 3, 1).dados]).toEqual([0x80]);
  });
});

describe('ZPL', () => {
  it('compressão ASCII: repetições, fim em branco (",") e em preto ("!")', () => {
    expect(comprimirLinhaZpl('FF000000')).toBe('HF,');
    expect(comprimirLinhaZpl('00FFFFFF')).toBe('H0!');
    // 45 = h (40) + K (5)
    expect(comprimirLinhaZpl('A' + 'B'.repeat(45) + 'C')).toBe('AhKBC');
    expect(comprimirLinhaZpl('ABCD')).toBe('ABCD');
  });

  it('linha igual à anterior vira ":"', () => {
    const b = bitmapVazio(8, 3);
    for (let y = 0; y < 3; y++) pintar(b, 0, y);
    expect(graficoZpl(b, false)).toBe('^GFA,3,3,1,80::');
  });

  it('1 = impresso (sem inverter) e ^PQ com a quantidade', () => {
    const zpl = texto(gerarZpl([{ bitmap: bitmapTeste(), quantidade: 40 }], cfg));
    expect(zpl).toContain('^PW400');
    expect(zpl).toContain('^LL240');
    // linha 1: "FF00" → HF, ; linha 2 toda em branco → ,
    expect(zpl).toContain('^FO0,0^GFA,4,4,2,HF,,^FS');
    expect(zpl).toContain('^PQ40');
    expect(zpl.match(/\^XA/g)).toHaveLength(1);
  });

  it('girar 180° e escuridão', () => {
    const zpl = texto(gerarZpl([{ bitmap: bitmapTeste(), quantidade: 1 }], { ...cfg, girar180: true, escuridao: 10 }));
    expect(zpl).toContain('^POI');
    expect(zpl.startsWith('~SD20')).toBe(true);
  });
});

describe('TSPL', () => {
  it('0 = impresso: o bitmap vai invertido, com SIZE, GAP e PRINT', () => {
    const bytes = gerarTspl([{ bitmap: bitmapTeste(), quantidade: 3 }], cfg);
    const cabecalho = texto(bytes);
    expect(cabecalho).toContain('SIZE 50 mm,30 mm');
    expect(cabecalho).toContain('GAP 2 mm,0 mm');
    expect(cabecalho).toContain('PRINT 1,3');
    const inicio = cabecalho.indexOf('BITMAP 0,0,2,2,0,') + 'BITMAP 0,0,2,2,0,'.length;
    expect([...bytes.slice(inicio, inicio + 4)]).toEqual([0x00, 0xff, 0xff, 0xff]);
  });

  it('"inverter cores" desfaz a inversão', () => {
    const bytes = gerarTspl([{ bitmap: bitmapTeste(), quantidade: 1 }], { ...cfg, inverter: true });
    const inicio = texto(bytes).indexOf('BITMAP 0,0,2,2,0,') + 'BITMAP 0,0,2,2,0,'.length;
    expect([...bytes.slice(inicio, inicio + 4)]).toEqual([0xff, 0x00, 0x00, 0x00]);
  });
});

describe('EPL / PPLB', () => {
  it('q/Q com gap em pontos, GW invertido e P com a quantidade', () => {
    const bytes = gerarEpl([{ bitmap: bitmapTeste(), quantidade: 5 }], cfg);
    const epl = texto(bytes);
    expect(epl).toContain('q400');
    expect(epl).toContain('Q240,16');
    expect(epl).toContain('P5');
    const inicio = epl.indexOf('GW0,0,2,2,') + 'GW0,0,2,2,'.length;
    expect([...bytes.slice(inicio, inicio + 4)]).toEqual([0x00, 0xff, 0xff, 0xff]);
  });
});

describe('agrupamento', () => {
  it('páginas iguais em sequência viram uma com quantidade', () => {
    const a = [{ posicao: 0, item: { 'produto.nome': 'A' } }];
    const b = [{ posicao: 0, item: { 'produto.nome': 'B' } }];
    const grupos = agruparPaginas([a, a, a, b, a]);
    expect(grupos.map((g) => g.quantidade)).toEqual([3, 1, 1]);
  });
});

describe('quebra de texto', () => {
  const medir = (s: string) => s.length; // 1 "ponto" por caractere

  it('palavras inteiras dentro da largura', () => {
    expect(quebrarTexto('parafuso sextavado zincado', 10, 3, medir)).toEqual(['parafuso', 'sextavado', 'zincado']);
  });

  it('reticências quando não cabe no número de linhas', () => {
    expect(quebrarTexto('parafuso sextavado zincado', 10, 2, medir)).toEqual(['parafuso', 'sextavado…']);
    expect(quebrarTexto('parafuso sextavado zincado', 9, 2, medir)).toEqual(['parafuso', 'sextavad…']);
  });

  it('palavra maior que a linha é cortada', () => {
    expect(quebrarTexto('abcdefghij', 4, 3, medir)).toEqual(['abcd', 'efgh', 'ij']);
  });
});
