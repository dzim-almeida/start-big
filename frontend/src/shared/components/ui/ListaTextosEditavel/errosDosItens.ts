/**
 * @fileoverview A regra dos itens do editor de listas (Spec 04B D14; 12B).
 * É a mesma do backend (Spec 04A §6.4), para o erro aparecer ao digitar.
 */

/**
 * Erros de cada item de uma lista (mesma regra do backend): vazio, longo
 * demais ou repetido (sem diferenciar maiúsculas e sem os espaços das pontas).
 * Devolve um texto por item, vazio quando o item está certo.
 */
export function errosDosItens(itens: string[], maxCaracteres: number): string[] {
  const vistos = new Map<string, number>();            // texto normalizado -> primeira posição
  return itens.map((item, indice) => {
    const limpo = item.trim();
    if (!limpo) return 'Preencha ou remova este item.';
    if (limpo.length > maxCaracteres) return `Até ${maxCaracteres} caracteres.`;
    const chave = limpo.toLocaleLowerCase('pt-BR');
    const primeiro = vistos.get(chave);
    if (primeiro !== undefined && primeiro !== indice) return 'Item repetido.';
    vistos.set(chave, indice);
    return '';
  });
}
