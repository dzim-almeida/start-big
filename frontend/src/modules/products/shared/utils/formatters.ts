export function formatCurrency(valueInCents: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valueInCents / 100).replace(/\s/g, ' ');
}

export function formatQuantity(qty: number): string {
  return `${qty} un`;
}