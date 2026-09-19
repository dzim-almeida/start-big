/**
 * O que a loja RECEBEU numa OS, para as três vias (A4, cupom HTML, ESC/POS)
 * fazerem a mesma conta — e a mesma conta que a tela e o backend.
 *
 * O caso normal é simples: adiantamento (limitado ao total) + soma dos
 * pagamentos do fechamento. O caso que quebrava é a OS REABERTA com "cliente
 * pagou": a reabertura zera `valor_entrada`, guarda tudo o que já entrou em
 * `credito_anterior` e MANTÉM as linhas antigas em `pagamentos`. As vias só
 * somavam as linhas — o recibo dizia "Total pago R$ 3.280" para um cliente
 * que tinha pago R$ 6.560 (achado da Fase 3 da marcenaria, 16/09/2026).
 *
 * Somar linhas + crédito também estaria errado: as linhas antigas JÁ estão
 * dentro do crédito. O que separa "linhas que o crédito já cobre" de
 * "pagamentos feitos depois da reabertura" é `adiantamentos_anteriores`: o
 * crédito é `linhas antigas + adiantamentos antigos`, e os adiantamentos são a
 * única parte dele que não está em `pagamentos`. Então
 * `linhas no crédito = crédito − adiantamentos_anteriores`, e
 * `pagamentos após = soma das linhas − linhas no crédito`. Exato, sem chute.
 *
 * A conta anterior (até 19/09/2026) fazia `max(0, soma das linhas − crédito)`.
 * Com adiantamento dentro do crédito, a subtração engolia o pagamento novo
 * quando ele era menor que o adiantamento antigo — o recibo dizia que a loja
 * tinha recebido menos do que recebeu. Mesmo defeito que o backend tinha no
 * `finalizar`, corrigido junto.
 *
 * `listarLinhas` diz à via se deve imprimir as linhas uma a uma (OS normal) ou
 * trocar por "Pago antes da reabertura" + "após a reabertura" (OS reaberta) —
 * imprimir as linhas antigas ao lado do crédito faria o leitor somar duas
 * vezes. Sem `credito_anterior`, tudo aqui devolve exatamente o que as vias
 * sempre calcularam.
 */
export interface RecebidoOS {
  /** `valor_entrada` cru (o que a via mostra em "Adiantamento (entrada)"). */
  adiantamento: number;
  /** Entrada limitada ao total — a parte que de fato abate. */
  adiantamentoUtilizado: number;
  /** Soma das linhas de `pagamentos`, como sempre foi. */
  somaPagamentos: number;
  /** `credito_anterior` (0 quando a OS nunca foi reaberta). */
  creditoAnterior: number;
  /** Pagamentos além do crédito — os feitos depois da reabertura. */
  pagamentosAposReabertura: number;
  /** O que a loja recebeu, no total. */
  totalRecebido: number;
  /** true = OS normal, imprime as linhas; false = OS reaberta, imprime o crédito. */
  listarLinhas: boolean;
}

export function calcularRecebidoOS(os: {
  valor_total?: number | null;
  valor_entrada?: number | null;
  credito_anterior?: number | null;
  adiantamentos_anteriores?: number | null;
  pagamentos?: ReadonlyArray<{ valor: number }> | null;
}): RecebidoOS {
  const adiantamento = os.valor_entrada ?? 0;
  const adiantamentoUtilizado = Math.min(adiantamento, os.valor_total ?? 0);
  const somaPagamentos = (os.pagamentos ?? []).reduce((acc, p) => acc + p.valor, 0);
  const creditoAnterior = os.credito_anterior ?? 0;
  const adiantamentosAnteriores = os.adiantamentos_anteriores ?? 0;

  if (creditoAnterior <= 0) {
    return {
      adiantamento,
      adiantamentoUtilizado,
      somaPagamentos,
      creditoAnterior: 0,
      pagamentosAposReabertura: 0,
      totalRecebido: adiantamentoUtilizado + somaPagamentos,
      listarLinhas: true,
    };
  }

  // Linhas que o crédito já cobre = crédito menos a parte que não é linha.
  // O `max(0, …)` de fora só protege de dado inconsistente (crédito menor que
  // as linhas antigas); em dado são ele não muda nada.
  const linhasNoCredito = Math.max(0, creditoAnterior - adiantamentosAnteriores);
  const pagamentosAposReabertura = Math.max(0, somaPagamentos - linhasNoCredito);
  return {
    adiantamento,
    adiantamentoUtilizado,
    somaPagamentos,
    creditoAnterior,
    pagamentosAposReabertura,
    totalRecebido: creditoAnterior + pagamentosAposReabertura + adiantamentoUtilizado,
    listarLinhas: false,
  };
}
