import { describe, expect, it } from 'vitest';

import { valoresDaEmbalagem, valoresDoProduto, valorDoCodigo } from '../campos';

const lata = {
  nome: 'Cerveja Lata 350ml',
  codigo_produto: 'CERV-350',
  codigo_barras: '7891000100103',
  estoque: { valor_varejo: 450 },
};
const fardo = { sigla: 'FD', descricao: 'Fardo com 12', fator: 12, codigo_barras: '17891000100100', preco: 4500, desconto_bp: null };

describe('etiqueta de embalagem', () => {
  it('sai com o código, o preço e o nome do fardo', () => {
    const v = valoresDaEmbalagem(lata, fardo);
    expect(v['produto.nome']).toBe('Cerveja Lata 350ml · Fardo com 12');
    expect(valorDoCodigo(v, 'produto.codigo_barras')).toBe('17891000100100');
    expect(v['preco.varejo']).toMatch(/45,00/);
    expect(v['embalagem.conteudo']).toBe('Contém 12 un');
    expect(v['preco.unidade_na_embalagem']).toMatch(/3,75 a unidade/);
  });

  it('fardo SEM código nunca imprime o código da unidade (o caixa venderia uma lata)', () => {
    const v = valoresDaEmbalagem(lata, { ...fardo, codigo_barras: null });
    expect(valorDoCodigo(v, 'produto.codigo_barras')).toBe('');
  });

  it('sem descrição, monta pela sigla e pela quantidade', () => {
    expect(valoresDaEmbalagem(lata, { ...fardo, descricao: null })['produto.nome']).toBe('Cerveja Lata 350ml · FD com 12');
  });

  it('a etiqueta da unidade continua igual (e ainda cai para o código interno sem EAN)', () => {
    const v = valoresDoProduto({ ...lata, codigo_barras: null });
    expect(valorDoCodigo(v, 'produto.codigo_barras')).toBe('CERV-350');
    expect(v['embalagem.conteudo']).toBeUndefined();
  });
});
