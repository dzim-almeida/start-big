/**
 * O aviso de virada de ano na inutilização.
 *
 * A regra vem do backend (`client_startbig.py`, campo `ano`) e do combinado
 * com a plataforma em 19/09/2026: a doc da Focus não lista `ano`, e ninguém
 * confirmou se ela honra o que mandamos ou assume o ano do envio. A única
 * regra que funciona nos dois casos é INUTILIZAR NO MESMO ANO em que a faixa
 * foi aberta -- uma faixa de dezembro inutilizada em janeiro pode ir para o
 * ano errado.
 *
 * O aviso só aparece quando importa: em dezembro (ainda dá tempo) e em
 * janeiro (o risco já se materializou para o que ficou). No resto do ano, um
 * aviso permanente viraria ruído, e ruído é como painel de aviso morre.
 *
 * `hoje` é parâmetro para o teste não depender do relógio.
 */
export interface AvisoViradaDeAno {
  nivel: 'atencao' | 'alerta';
  titulo: string;
  detalhe: string;
}

export function avisoViradaDeAno(hoje: Date = new Date()): AvisoViradaDeAno | null {
  const mes = hoje.getMonth(); // 0 = janeiro, 11 = dezembro
  const ano = hoje.getFullYear();

  if (mes === 11) {
    return {
      nivel: 'atencao',
      titulo: `Inutilize as faixas deste ano ainda em ${ano}`,
      detalhe:
        'Uma faixa aberta em dezembro e inutilizada em janeiro pode ser registrada no ano ' +
        'errado. Resolva os buracos abaixo antes da virada.',
    };
  }

  if (mes === 0) {
    return {
      nivel: 'alerta',
      titulo: `Faixas abertas em ${ano - 1} devem ter sido inutilizadas em ${ano - 1}`,
      detalhe:
        'Se algum buraco abaixo é do ano passado, confirme com o contador antes de ' +
        'inutilizar: o registro pode sair no ano corrente.',
    };
  }

  return null;
}
