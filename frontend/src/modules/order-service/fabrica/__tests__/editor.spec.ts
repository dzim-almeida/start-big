import { describe, expect, it } from 'vitest';

import type { InsumoBusca, OrcamentoRead } from '../types/fabrica.types';
import { editavelDe, escritaDe, materialDe, novoAmbiente, problemasDe, totaisDe } from '../utils/editor';

const MDF: InsumoBusca = {
  id: 7, nome: 'MDF Branco 15mm', codigo_produto: 'MDF-15', unidade_medida: 'CH',
  unidade_consumo: 'M2', consumo_por_unidade: 2750 * 1850, sofre_perda: true, custo_unitario: 30000,
};

function orcamentoDoServidor(): OrcamentoRead {
  return {
    id: 1, versao: 1, situacao: 'RASCUNHO', total: 240000, criado_em: '', enviado_em: null, aprovado_em: null,
    os_id: 1, numero_os: 'OS-2026-000001', perda_bp: 1000, sinal_bp: 5000, sinal_valor: 120000,
    validade: '2026-10-20', custo_total: 25946, observacao: null, aprovado_por: null, recusado_motivo: null,
    editavel: true, insumos: [],
    ambientes: [{
      id: 1, nome: 'Cozinha',
      moveis: [{
        id: 1, nome: 'Armário aéreo', largura_mm: 1800, altura_mm: 700, profundidade_mm: 350, medidas: '1800×700×350',
        preco_venda: 240000, terceirizado: false, custo_terceiro: null, custo: 25946,
        materiais: [{
          id: 9, produto_id: 7, descricao: 'MDF Branco 15mm', consumo: 4_000_000, unidade_consumo: 'M2',
          consumo_por_unidade: 2750 * 1850, sofre_perda: true, unidade_medida: 'CH', custo_unitario: 30000, custo: 25946,
        }],
      }],
    }],
  };
}

describe('editor do orçamento', () => {
  it('servidor → tela → servidor devolve o mesmo (sem alteração fantasma)', () => {
    const escrita = escritaDe(editavelDe(orcamentoDoServidor()));
    expect(escrita).toEqual({
      perda_bp: 1000, sinal_bp: 5000, validade: '2026-10-20', observacao: null,
      ambientes: [{
        nome: 'Cozinha',
        moveis: [{
          nome: 'Armário aéreo', largura_mm: 1800, altura_mm: 700, profundidade_mm: 350, preco_venda: 240000,
          terceirizado: false, custo_terceiro: null,
          materiais: [{ id: 9, produto_id: 7, consumo: 4_000_000 }],
        }],
      }],
    });
  });

  it('prévia bate com o servidor: custo, margem e sinal', () => {
    const totais = totaisDe(editavelDe(orcamentoDoServidor()));
    expect(totais).toEqual({ total: 240000, custo: 25946, margemBp: 8919, sinal: 120000 });
  });

  it('material novo vai sem id (o servidor copia o custo de hoje)', () => {
    const edit = editavelDe(orcamentoDoServidor());
    const m = materialDe(MDF);
    m.quantidade = 1.5;
    edit.ambientes[0]!.moveis[0]!.materiais.push(m);
    const linha = escritaDe(edit).ambientes[0]!.moveis[0]!.materiais[1];
    expect(linha).toEqual({ id: null, produto_id: 7, consumo: 1_500_000 });
  });

  it('aponta o que falta antes de salvar', () => {
    const edit = editavelDe(orcamentoDoServidor());
    edit.ambientes.push(novoAmbiente(''));
    edit.ambientes[0]!.moveis[0]!.materiais[0]!.quantidade = null;
    expect(problemasDe(edit)).toEqual([
      'Cozinha — Armário aéreo: informe quanto de "MDF Branco 15mm" vai.',
      'Ambiente 2: dê um nome ao ambiente.',
      'Ambiente 2 — móvel 1: dê um nome ao móvel.',
    ]);
  });
});
