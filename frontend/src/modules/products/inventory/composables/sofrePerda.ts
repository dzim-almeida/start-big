/**
 * "Sofre perda no orçamento" (Spec 04A/04B da marcenaria).
 *
 * O campo só viaja no cadastro do produto no segmento com orçamento técnico
 * (hoje, a marcenaria). Nos outros segmentos o corpo enviado fica IDÊNTICO ao
 * de antes (Spec 04B, D3): o backend aceitaria o campo, mas não há por que
 * mudar o que as lojas em produção mandam.
 *
 * Função pura e separada para dar para testar sem montar o modal de produto.
 */
export function campoSofrePerda(
  temOrcamentoTecnico: boolean,   // o segmento declara `orcamento_tecnico`?
  sofrePerda: boolean | undefined, // valor da caixa no formulário
): { sofre_perda?: boolean } {
  // Sem a capacidade: nada é acrescentado ao corpo.
  if (!temOrcamentoTecnico) return {};
  // Com a capacidade: manda o valor da caixa (desmarcada = false).
  return { sofre_perda: Boolean(sofrePerda) };
}
