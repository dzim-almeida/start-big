import { describe, expect, it } from 'vitest';

import {
  descontosRegraDaVenda,
  multiplicadorDaLinha,
  precoDaEmbalagem,
  precoUnitarioNaEmbalagem,
  quantidadeDaLinha,
  regraDaLinha,
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

describe('regraDaLinha', () => {
  it('sem regra (ou preço manual) não imprime nada', () => {
    expect(regraDaLinha({})).toBeNull();
    expect(regraDaLinha({ regra_preco: 'MANUAL', regra_descricao: 'x' })).toBeNull();
  });

  it('R1/R3 trazem texto e valor; R2 só o texto', () => {
    expect(regraDaLinha({ regra_preco: 'R1', regra_descricao: 'Preço de 1 FD (15 un)', desconto_regra: 1750 }))
      .toEqual({ texto: 'Preço de 1 FD (15 un)', desconto: 1750 });
    expect(regraDaLinha({ regra_preco: 'R2', regra_descricao: 'A partir de 6 un: R$ 3,80', desconto_regra: 0 }))
      .toEqual({ texto: 'A partir de 6 un: R$ 3,80', desconto: 0 });
  });

  it('descontosRegraDaVenda: orçamento e backend antigo valem 0', () => {
    expect(descontosRegraDaVenda({ descontos: 10 })).toBe(0);
    expect(descontosRegraDaVenda({ descontos_regra: 1750 })).toBe(1750);
  });
});

describe('linha a granel (venda fracionada)', () => {
  it('3,5 kg sai com vírgula e unidade; UN segue como sempre', () => {
    expect(quantidadeDaLinha({ quantidade: 3.5, unidade_medida: 'KG' })).toBe('3,5 kg');
    expect(multiplicadorDaLinha({ quantidade: 3.5, unidade_medida: 'KG' })).toBe('3,5 kg x');
    expect(quantidadeDaLinha({ quantidade: 3, unidade_medida: 'UN' })).toBe('3');
    expect(multiplicadorDaLinha({ quantidade: 3, unidade_medida: 'UN' })).toBe('3x');
    expect(quantidadeDaLinha({ quantidade: 2, sigla_embalagem: 'FD', fator_embalagem: 12, unidade_medida: 'KG' })).toBe('2 FD');
  });
});
