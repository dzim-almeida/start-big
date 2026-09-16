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
 * dentro do crédito. A conta certa é a que `finalizar_ordem_servico` usa para
 * validar o fechamento: crédito + max(0, soma das linhas − crédito) + entrada.
 * O `max` é o que separa "linhas que o crédito já cobre" de "pagamentos feitos
 * depois da reabertura", sem precisar saber qual linha é qual.
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
  pagamentos?: ReadonlyArray<{ valor: number }> | null;
}): RecebidoOS {
  const adiantamento = os.valor_entrada ?? 0;
  const adiantamentoUtilizado = Math.min(adiantamento, os.valor_total ?? 0);
  const somaPagamentos = (os.pagamentos ?? []).reduce((acc, p) => acc + p.valor, 0);
  const creditoAnterior = os.credito_anterior ?? 0;

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

  const pagamentosAposReabertura = Math.max(0, somaPagamentos - creditoAnterior);
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
