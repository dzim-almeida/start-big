/**
 * @fileoverview Formatação de quantidade com unidade de medida.
 *
 * Existe pelo mesmo motivo do `formatCurrency`: a unidade estava escrita à mão
 * em cada tela ("{{ quantidade }} un"), sempre como "un", ignorando o
 * `unidade_medida` que o produto já traz do cadastro.
 *
 * Não era só rótulo errado. O estoque é fracionado (`Float` no banco), então uma
 * sacola comprada por peso aparecia como **"2,5 un"** — que se lê como duas
 * sacolas e meia, quando são 2,5 kg e podem ser 200 sacolas. Num inventário ou
 * numa conferência de balcão, isso é erro de leitura sobre o número que serve
 * justamente para contar mercadoria.
 */

/**
 * Unidades vendidas a granel, em que a fração É o normal.
 *
 * ⚠️ ESPELHO de `UNIDADES_FRACIONAVEIS` em
 * backend-fastapi/app/services/quantidade_venda.py: é o servidor que aceita ou
 * recusa 3,5 numa venda. Divergir faz a tela oferecer o que o servidor nega.
 */
export const UNIDADES_FRACIONADAS = new Set(['KG', 'G', 'L', 'ML', 'M', 'CM', 'M2', 'M3']);

/** Casas da quantidade quebrada — as mesmas do backend (`app/schemas/quantidade.py`). */
export const CASAS_QUANTIDADE = 3;

function siglaNormalizada(unidade?: string | null): string {
  return (unidade ?? UNIDADE_PADRAO).trim().toUpperCase().replace('²', '2').replace('³', '3');
}

/** Fallback: sem unidade cadastrada, é peça — o caso de informática e oficina. */
const UNIDADE_PADRAO = 'UN';

/**
 * Só a sigla, minúscula. Para quando o número já foi formatado à parte — é o
 * caso do painel de transações, onde ele leva sinal (+/−) na frente.
 */
export function siglaUnidade(unidade?: string | null): string {
  return ((unidade ?? '').trim() || UNIDADE_PADRAO).toLowerCase();
}

export function unidadeEhFracionada(unidade?: string | null): boolean {
  return UNIDADES_FRACIONADAS.has(siglaNormalizada(unidade));
}

/**
 * 3 casas, como o servidor guarda: 1,1 + 1 em ponto flutuante dá
 * 2,1000000000000001, e esse resto iria na requisição.
 */
export function normalizarQuantidade(quantidade: number): number {
  return Math.round(quantidade * 10 ** CASAS_QUANTIDADE) / 10 ** CASAS_QUANTIDADE;
}

/**
 * Só o número, para o CAMPO de quantidade: "3,5" (fracionada) ou "3" (inteira).
 *
 * Sem separador de milhar, de propósito: o campo relê o que mostra, e "1.234,5"
 * não volta a ser número. É também o que a linha em UN sempre exibiu ("1000").
 */
export function formatarNumeroQuantidade(quantidade: number | null | undefined, unidade?: string | null): string {
  const valor = Number(quantidade ?? 0);
  const seguro = Number.isFinite(valor) ? valor : 0;
  if (!unidadeEhFracionada(unidade)) return String(Math.round(seguro));
  return String(normalizarQuantidade(seguro)).replace('.', ',');
}

/**
 * O número como veio, em português: "3,5" ou "3". Para onde a unidade não
 * chega — o item da nota no drawer fiscal. Inteiro sai igual ao de sempre.
 */
export function formatarQuantidadeSemUnidade(quantidade: number | null | undefined): string {
  const valor = Number(quantidade ?? 0);
  return String(normalizarQuantidade(Number.isFinite(valor) ? valor : 0)).replace('.', ',');
}

/**
 * Formata a quantidade com a unidade do cadastro.
 *
 * Casas decimais seguem a unidade, e não o valor: "2,5 kg" descreve o mundo,
 * "2,5 un" não descreve nada. Em unidade inteira o número é arredondado; em
 * unidade de peso/volume, mostra até 3 casas — e corta os zeros à direita, para
 * "2 kg" não virar "2,000 kg".
 *
 * @param quantidade  valor numérico do estoque/item
 * @param unidade     `produto.unidade_medida` (ou do item da OS). Vazio = "UN".
 */
export function formatarQuantidade(
  quantidade: number | null | undefined,
  unidade?: string | null,
): string {
  const valor = Number(quantidade ?? 0);
  const seguro = Number.isFinite(valor) ? valor : 0;

  const sigla = (unidade ?? '').trim() || UNIDADE_PADRAO;

  const texto = unidadeEhFracionada(sigla)
    ? seguro.toLocaleString('pt-BR', { maximumFractionDigits: 3 })
    : Math.round(seguro).toLocaleString('pt-BR');

  return `${texto} ${sigla.toLowerCase()}`;
}
