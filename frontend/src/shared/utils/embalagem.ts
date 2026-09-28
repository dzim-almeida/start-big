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

interface LinhaComEmbalagem {
  quantidade: number;
  sigla_embalagem?: string | null;
  fator_embalagem?: number | null;
}

/** "2 FD" na linha de embalagem; só "2" na de unidade (impressões, G4). */
export function quantidadeDaLinha(item: LinhaComEmbalagem): string {
  return item.sigla_embalagem && (item.fator_embalagem ?? 1) > 1
    ? `${item.quantidade} ${item.sigla_embalagem}`
    : `${item.quantidade}`;
}

/** "(24 un)" embaixo da linha de embalagem; nulo na de unidade (G4). */
export function unidadesDaLinha(item: LinhaComEmbalagem): string | null {
  const fator = item.fator_embalagem ?? 1;
  return item.sigla_embalagem && fator > 1 ? `(${item.quantidade * fator} un)` : null;
}

/** Começo da linha do cupom: "2x" na unidade (como sempre foi), "2 FD x" na embalagem. */
export function multiplicadorDaLinha(item: LinhaComEmbalagem): string {
  const q = quantidadeDaLinha(item);
  return q === `${item.quantidade}` ? `${q}x` : `${q} x`;
}

interface LinhaComRegra {
  regra_preco?: string | null;
  regra_descricao?: string | null;
  desconto_regra?: number | null;
}

/**
 * Regra de preço por quantidade na via impressa (§6.1): o cliente vê por que
 * pagou menos. R1/R3 trazem o valor ("Preço de 1 FD (15 un)", −17,50); a R2 só
 * o texto, porque o preço dela já é o unitário da linha. Nulo sem regra —
 * a linha sai exatamente como antes.
 */
export function regraDaLinha(item: LinhaComRegra): { texto: string; desconto: number } | null {
  if (!item.regra_preco || item.regra_preco === 'MANUAL' || !item.regra_descricao) return null;
  return { texto: item.regra_descricao, desconto: item.desconto_regra ?? 0 };
}

/** Soma das regras na venda; orçamento (e backend antigo) não tem: 0. */
export function descontosRegraDaVenda(venda: object): number {
  return 'descontos_regra' in venda ? Number(venda.descontos_regra) || 0 : 0;
}
