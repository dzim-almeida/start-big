export function formatCentavosToBRL(valueInCents: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valueInCents / 100);
}

export function toCents(value?: number): number | undefined {
  if (value === null || value === undefined) return undefined;
  return Math.round(value * 100);
}
