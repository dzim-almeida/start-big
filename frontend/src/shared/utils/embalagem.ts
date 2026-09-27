/**
 * @fileoverview Regras de embalagem (fardo/caixa) que mais de uma tela usa:
 * cadastro, card do estoque, etiqueta — e o PDV, na fase 3.
 * Ver docs/produto-embalagens-plano.md (D5, D14, A4, D21).
 */

interface EmbalagemPreco {
  fator: number;
  preco: number | null;
  desconto_bp: number | null;
}

/**
 * Preço da embalagem, em centavos: o próprio (D14); senão fator × unidade com
 * o desconto (A4); senão fator × unidade (D5). Arredonda para o centavo.
 */
export function precoDaEmbalagem(embalagem: EmbalagemPreco, precoUnidade: number): number {
  if (embalagem.preco != null) return embalagem.preco;
  const cheio = embalagem.fator * precoUnidade;
  if (embalagem.desconto_bp) return Math.round((cheio * (10000 - embalagem.desconto_bp)) / 10000);
  return cheio;
}

/** Preço de cada unidade dentro da embalagem ("R$ 3,75 a lata"), em centavos. */
export function precoUnitarioNaEmbalagem(embalagem: EmbalagemPreco, precoUnidade: number): number {
  return Math.round(precoDaEmbalagem(embalagem, precoUnidade) / embalagem.fator);
}

interface EmbalagemSaldo {
  sigla: string;
  fator: number;
  ativo: boolean;
  vende_no_pdv: boolean;
}

/**
 * O saldo em embalagem fechada para mostrar DISCRETO no card (D21):
 * "= 10 FD". Usa a MENOR embalagem de verdade (fator ≥ 2) ativa e vendida
 * no caixa — é a que o balconista conta. Nulo quando não há o que mostrar.
 */
export function saldoEmEmbalagem(quantidade: number, embalagens: EmbalagemSaldo[] | undefined): string | null {
  const alvo = (embalagens ?? [])
    .filter((e) => e.ativo && e.vende_no_pdv && e.fator >= 2)
    .sort((a, b) => a.fator - b.fator)[0];
  if (!alvo || quantidade <= 0) return null;
  const fechadas = Math.floor(quantidade / alvo.fator);
  return `= ${fechadas} ${alvo.sigla}`;
}
