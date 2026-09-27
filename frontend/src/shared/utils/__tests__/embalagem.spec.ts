import { describe, expect, it } from 'vitest';

import {
  multiplicadorDaLinha,
  precoDaEmbalagem,
  precoUnitarioNaEmbalagem,
  quantidadeDaLinha,
  saldoEmEmbalagem,
  unidadesDaLinha,
} from '../embalagem';

describe('preço da embalagem', () => {
  it('preço próprio vale mais que tudo', () => {
    expect(precoDaEmbalagem({ fator: 12, preco: 4500, desconto_bp: null }, 450)).toBe(4500);
  });
  it('desconto sobre fator × unidade', () => {
    // 12 × 4,50 = 54,00; −5% = 51,30
    expect(precoDaEmbalagem({ fator: 12, preco: null, desconto_bp: 500 }, 450)).toBe(5130);
  });
  it('sem preço nem desconto = fator × unidade', () => {
    expect(precoDaEmbalagem({ fator: 15, preco: null, desconto_bp: null }, 400)).toBe(6000);
  });
  it('preço da unidade dentro da embalagem', () => {
    expect(precoUnitarioNaEmbalagem({ fator: 12, preco: 4500, desconto_bp: null }, 450)).toBe(375);
  });
});

describe('saldo em embalagem', () => {
  const emb = (sigla: string, fator: number, extra = {}) => ({ sigla, fator, ativo: true, vende_no_pdv: true, ...extra });

  it('usa a menor embalagem de verdade e arredonda para baixo', () => {
    expect(saldoEmEmbalagem(125, [emb('CX', 24), emb('FD', 12)])).toBe('= 10 FD');
  });
  it('ignora código adicional (fator 1), inativa e só de entrada', () => {
    expect(saldoEmEmbalagem(50, [emb('UN', 1), emb('FD', 6, { ativo: false }), emb('CX', 24, { vende_no_pdv: false })])).toBeNull();
  });
  it('sem embalagem ou sem estoque, nada', () => {
    expect(saldoEmEmbalagem(0, [emb('FD', 12)])).toBeNull();
    expect(saldoEmEmbalagem(30, undefined)).toBeNull();
  });
});

describe('quantidade da linha nas impressões (G4)', () => {
  const fardo = { quantidade: 2, sigla_embalagem: 'FD', fator_embalagem: 12 };
  const unidade = { quantidade: 3, sigla_embalagem: null, fator_embalagem: 1 };

  it('linha de fardo sai "2 FD (24 un)"', () => {
    expect(quantidadeDaLinha(fardo)).toBe('2 FD');
    expect(unidadesDaLinha(fardo)).toBe('(24 un)');
    expect(multiplicadorDaLinha(fardo)).toBe('2 FD x');
  });

  it('linha de unidade sai exatamente como antes', () => {
    expect(quantidadeDaLinha(unidade)).toBe('3');
    expect(unidadesDaLinha(unidade)).toBeNull();
    expect(multiplicadorDaLinha(unidade)).toBe('3x');
    // Backend antigo, sem os campos novos.
    expect(multiplicadorDaLinha({ quantidade: 1 })).toBe('1x');
  });
});
