/**
 * Selo do pagamento combinado para depois ("fiado / a prazo", boleto).
 *
 * Existe porque, no PDV e na finalização da OS, um pagamento a prazo e um
 * pago na hora apareciam IGUAIS na lista: quem lançava os dois como "recebido"
 * por engano não tinha como perceber antes de finalizar (caso do monitor de
 * R$ 400 com R$ 200 para o dia 30, 12/10/2026).
 *
 * `vencimento` vem como 'AAAA-MM-DD' (o que vai para a API). Lido como texto,
 * e não com `new Date`, para o fuso não puxar a data um dia para trás.
 */
export function rotuloAReceber(vencimento?: string | null, hoje: Date = new Date()): string | null {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(vencimento ?? '');
  if (!partes) return null;
  const [, ano, mes, dia] = partes;
  const mesmoAno = Number(ano) === hoje.getFullYear();
  return `A receber em ${dia}/${mes}${mesmoAno ? '' : `/${ano}`}`;
}
