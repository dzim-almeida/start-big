/**
 * Spec 03B — o que a comanda manda ao `POST /ordens-servico`.
 */
import { describe, expect, it } from 'vitest';

import { montarOS, textoDoPedido, type PayloadLavagem } from '../services/comanda.service';

/** O corpo do POST, só com o que os testes leem. */
interface Corpo {
  dados_adicionais: Record<string, unknown>;
  data_previsao: string | null;
  objeto: Record<string, unknown>;
  funcionario_id: number | null;
  defeito_relatado: string;
}

const BASE: PayloadLavagem = {
  cliente_id: 7,
  funcionario_id: 3,
  tipo_veiculo: 'carro',
  placa: 'ABC1D23',
  modelo: ' Gol ',
  marca: '',
  cor: 'Prata',
  dados_objeto: { porte: 'Hatch', chassi: 'X' },
  porte: 'SUV',
  itens: [
    { servico_id: 1, nome: 'Lavagem completa', valor: 6000 },
    { servico_id: 2, nome: 'Cera', valor: 3000 },
  ],
  avarias: ['Riscos na pintura'],
  observacao: '',
  previsao: new Date('2026-11-12T15:00:00Z'),
};

describe('montarOS', () => {
  it('itens de serviço do catálogo com o preço da comanda', () => {
    const corpo = montarOS(BASE) as { itens: Record<string, unknown>[] };
    expect(corpo.itens).toEqual([
      { tipo: 'SERVICO', item_id: 1, nome: 'Lavagem completa', unidade_medida: 'UN', quantidade: 1, valor_unitario: 6000 },
      { tipo: 'SERVICO', item_id: 2, nome: 'Cera', unidade_medida: 'UN', quantidade: 1, valor_unitario: 3000 },
    ]);
  });

  it('tipo, avarias e previsão na OS; porte novo no veículo sem perder o resto', () => {
    const corpo = montarOS(BASE) as unknown as Corpo;
    expect(corpo.dados_adicionais).toEqual({ tipo_trabalho: 'carro', avarias: ['Riscos na pintura'] });
    expect(corpo.data_previsao).toBe('2026-11-12T15:00:00.000Z');
    expect(corpo.objeto).toEqual({
      numero_serie: 'ABC1D23', modelo: 'Gol', marca: '', cor: 'Prata',
      dados_adicionais: { porte: 'SUV', chassi: 'X' },
    });
    expect(corpo.funcionario_id).toBe(3);
  });

  it('sem lavador: OS sem responsável; sem previsão: null', () => {
    const corpo = montarOS({ ...BASE, funcionario_id: null, previsao: null }) as unknown as Corpo;
    expect(corpo.funcionario_id).toBeNull();
    expect(corpo.data_previsao).toBeNull();
  });

});

describe('textoDoPedido (defeito_relatado é obrigatório na OS)', () => {
  it('os serviços; sem nada: "Lavagem"', () => {
    expect(textoDoPedido(BASE.itens)).toBe('Lavagem completa, Cera');
    expect(textoDoPedido([])).toBe('Lavagem');
  });
  it('a observação (pertences) não vira o pedido', () => {
    const corpo = montarOS({ ...BASE, observacao: 'óculos no porta-luvas' }) as unknown as Corpo;
    expect(corpo.defeito_relatado).toBe('Lavagem completa, Cera');
    expect(corpo.dados_adicionais.pertences).toBe('óculos no porta-luvas');
  });
});
