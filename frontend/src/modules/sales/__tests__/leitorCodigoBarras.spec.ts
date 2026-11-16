import { describe, expect, it } from 'vitest';

import { resolverPorCodigoExato } from '../leitorCodigoBarras.util';
import type { ProductSaleListItem } from '../schemas/productSale.schema';

function produto(id: number, extra: Partial<ProductSaleListItem[number]> = {}): ProductSaleListItem[number] {
  return {
    id,
    nome: `Produto ${id}`,
    sku: `SKU-${id}`,
    codigo_barras: null,
    preco: 450,
    estoque: 100,
    embalagens: [],
    so_embalagem_fechada: false,
    ...extra,
  };
}

const cerveja = produto(1, {
  codigo_barras: '7891000000001',
  embalagens: [
    { id: 10, sigla: 'FD', fator: 12, codigo_barras: '17891000000008', preco: 4800 },
    { id: 11, sigla: 'UN', fator: 1, codigo_barras: '7891000000999', preco: 450 },
  ],
});

describe('leitor de código de barras com embalagens', () => {
  it('o código da unidade continua lançando a unidade', () => {
    const r = resolverPorCodigoExato('7891000000001', [cerveja]);
    expect(r).toEqual({ tipo: 'unico', produto: cerveja });
  });

  it('o código do fardo lança o fardo', () => {
    const r = resolverPorCodigoExato('17891000000008', [cerveja]);
    expect(r.tipo).toBe('unico');
    if (r.tipo === 'unico') expect(r.embalagem?.sigla).toBe('FD');
  });

  it('código adicional de fator 1 é a própria unidade (D3)', () => {
    const r = resolverPorCodigoExato('7891000000999', [cerveja]);
    expect(r).toEqual({ tipo: 'unico', produto: cerveja });
  });

  it('código que bate em produto e em embalagem de outro é ambíguo', () => {
    const outro = produto(2, { codigo_barras: '17891000000008' });
    expect(resolverPorCodigoExato('17891000000008', [cerveja, outro])).toEqual({ tipo: 'ambiguo', quantos: 2 });
  });

  it('sem embalagens (recurso desligado) nada muda', () => {
    const semEmb = produto(3, { codigo_barras: '789' });
    expect(resolverPorCodigoExato('789', [semEmb])).toEqual({ tipo: 'unico', produto: semEmb });
    expect(resolverPorCodigoExato('17891000000008', [semEmb])).toEqual({ tipo: 'nenhum' });
  });
});
