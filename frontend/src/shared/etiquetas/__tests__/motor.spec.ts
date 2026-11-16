import { describe, expect, it } from 'vitest';

import { gtinValido, resolverCodigo, digitoVerificadorGs1 } from '../codigoBarras';
import { problemasDaPagina, tamanhoDoPapel, posicaoNaPagina, type PaginaEtiqueta } from '../modelo';
import { paginar, expandir } from '../paginacao';
import { gerarElementos } from '../layoutAuto';
import { PRESETS } from '../presets';
import { valoresDoProduto, valorDoCodigo } from '../campos';

const bobina50x30: PaginaEtiqueta = {
  tipo: 'bobina', largura_mm: 50, altura_mm: 30, colunas: 1,
  espaco_colunas_mm: 0, espaco_linhas_mm: 0, margem_esq_mm: 0, margem_topo_mm: 0, folha: null,
};

describe('código de barras', () => {
  it('calcula o dígito verificador GS1', () => {
    expect(digitoVerificadorGs1('789100010010')).toBe(3);
    expect(gtinValido('7891000100103')).toBe(true);
    expect(gtinValido('7891000100104')).toBe(false);
  });

  it('auto escolhe pela forma do valor', () => {
    expect(resolverCodigo('7891000100103')?.simbologia).toBe('EAN13');
    expect(resolverCodigo('17891000100100')?.simbologia).toBe('ITF14');
    expect(resolverCodigo('PRD-0001')?.simbologia).toBe('CODE128');
    expect(resolverCodigo('   ')).toBeNull();
  });

  it('EAN com dígito errado NUNCA sai como EAN — cai para Code 128 e avisa', () => {
    const auto = resolverCodigo('7891000100104');
    expect(auto?.simbologia).toBe('CODE128');

    const forcado = resolverCodigo('7891000100104', 'EAN13');
    expect(forcado?.simbologia).toBe('CODE128');
    expect(forcado?.aviso).toContain('EAN-13');
  });

  it('Code 128 tira acento em vez de quebrar', () => {
    expect(resolverCodigo('Peça-01')?.valor).toBe('Peca-01');
  });
});

describe('campos', () => {
  it('sem EAN, o código de barras cai para o código interno', () => {
    const valores = valoresDoProduto({ nome: 'X', codigo_produto: 'INT-9', codigo_barras: null });
    expect(valorDoCodigo(valores, 'produto.codigo_barras')).toBe('INT-9');
  });

  it('preço sai formatado a partir dos centavos', () => {
    const valores = valoresDoProduto({ nome: 'X', estoque: { valor_varejo: 1290 } });
    expect(valores['preco.varejo']).toMatch(/12,90/);
  });
});

describe('página', () => {
  it('bobina de 3 colunas: o papel é o rolo inteiro × uma etiqueta', () => {
    const pagina = { ...bobina50x30, largura_mm: 33, altura_mm: 22, colunas: 3, espaco_colunas_mm: 2.5, margem_esq_mm: 1.5 };
    expect(tamanhoDoPapel(pagina)).toEqual({ largura_mm: 107, altura_mm: 22 });
    expect(posicaoNaPagina(pagina, 2)).toEqual({ x: 1.5 + 2 * 35.5, y: 0 });
  });

  it('folha que não comporta as colunas é recusada', () => {
    const pagina: PaginaEtiqueta = {
      ...bobina50x30, tipo: 'folha', largura_mm: 66.7, altura_mm: 25.4, colunas: 4,
      espaco_colunas_mm: 3.2, margem_esq_mm: 4.8, margem_topo_mm: 12.7,
      folha: { largura_mm: 215.9, altura_mm: 279.4, linhas: 10 },
    };
    expect(problemasDaPagina(pagina)[0]).toContain('colunas');
  });
});

describe('paginação', () => {
  const folha30 = PRESETS.find((p) => p.chave === 'preset:pimaco-6180')!.definicao.pagina;

  it('pular N posições começa a primeira folha depois delas', () => {
    const paginas = paginar(folha30, ['a', 'b', 'c'], 28);
    expect(paginas[0].map((p) => p.posicao)).toEqual([28, 29]);
    expect(paginas[1]).toEqual([{ posicao: 0, item: 'c' }]);
  });

  it('na bobina, pular é ignorado e cada fileira é uma página', () => {
    const paginas = paginar(bobina50x30, ['a', 'b'], 5);
    expect(paginas).toEqual([[{ posicao: 0, item: 'a' }], [{ posicao: 0, item: 'b' }]]);
  });

  it('expande pela quantidade, na ordem da fila', () => {
    expect(expandir([{ item: 'a', quantidade: 2 }, { item: 'b', quantidade: 1 }, { item: 'c', quantidade: 0 }])).toEqual(['a', 'a', 'b']);
  });
});

describe('presets e layout automático', () => {
  it.each(PRESETS.map((p) => [p.nome, p] as const))('%s cabe no papel e todo elemento cabe na etiqueta', (_, preset) => {
    const { pagina, elementos } = preset.definicao;
    expect(problemasDaPagina(pagina)).toEqual([]);
    for (const el of elementos) {
      expect(el.x + el.w).toBeLessThanOrEqual(pagina.largura_mm + 0.5);
      expect(el.y + el.h).toBeLessThanOrEqual(pagina.altura_mm + 0.5);
    }
  });

  it('etiqueta larga e baixa põe as barras numa coluna à direita', () => {
    const elementos = gerarElementos({ ...bobina50x30, largura_mm: 100, altura_mm: 30 }, { blocos: ['nome', 'preco_varejo', 'barras'] });
    const barras = elementos.find((e) => e.tipo === 'barras')!;
    expect(barras.x).toBeGreaterThan(50);
    expect(barras.h).toBeGreaterThan(20);
  });

  it('respeita só os blocos escolhidos', () => {
    const elementos = gerarElementos(bobina50x30, { blocos: ['nome'] });
    expect(elementos).toHaveLength(1);
    expect(elementos[0]).toMatchObject({ tipo: 'texto', campo: 'produto.nome' });
  });
});
