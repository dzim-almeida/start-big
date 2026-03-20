/**
 * Formata valor em centavos para moeda BRL.
 * Ex: 15000 → "R$ 150,00"
 */
export function formatCurrency(valueInCents: number): string {
  const reais = valueInCents / 100;
  return reais.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

/**
 * Formata centavos para string de input (sem prefixo R$).
 * Ex: 15000 → "150,00"
 */
export function formatCentsToInput(valueInCents: number): string {
  const reais = valueInCents / 100;
  return reais.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Converte string de moeda formatada para centavos.
 * Ex: "150,00" → 15000
 */
export function parseCurrencyToCents(value: string): number {
  const cleaned = value
    .replace(/[R$\s.]/g, '')
    .replace(',', '.');
  const parsed = parseFloat(cleaned);
  if (isNaN(parsed)) return 0;
  return Math.round(parsed * 100);
}
