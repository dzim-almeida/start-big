import { computed, type Ref } from 'vue';
import { parseCurrencyToCents, formatCurrency } from '@/shared/utils/finance';
import type { OSItemForm } from './useOSFormState';

export function useOSFinancials(
  itens: Ref<OSItemForm[]>,
  desconto: Ref<string>,
  valorEntrada?: Ref<string>
) {
  const subtotal = computed(() => {
    return itens.value.reduce((acc, item) => {
      return acc + (item.quantidade * item.valor_unitario);
    }, 0);
  });

  const valorDesconto = computed(() => {
    return parseCurrencyToCents(desconto.value);
  });

  const valorEntradaCents = computed(() => {
    if (!valorEntrada) return 0;
    return parseCurrencyToCents(valorEntrada.value);
  });

  const valorTotal = computed(() => {
    const total = subtotal.value - valorDesconto.value;
    return total > 0 ? total : 0;
  });

  const valorRestante = computed(() => {
    const restante = valorTotal.value - valorEntradaCents.value;
    return restante > 0 ? restante : 0;
  });

  const subtotalFormatted = computed(() => formatCurrency(subtotal.value));
  const descontoFormatted = computed(() => formatCurrency(valorDesconto.value));
  const totalFormatted = computed(() => formatCurrency(valorTotal.value));
  const entradaFormatted = computed(() => formatCurrency(valorEntradaCents.value));
  const restanteFormatted = computed(() => formatCurrency(valorRestante.value));

  return {
    subtotal,
    valorDesconto,
    valorEntradaCents,
    valorTotal,
    valorRestante,
    subtotalFormatted,
    descontoFormatted,
    totalFormatted,
    entradaFormatted,
    restanteFormatted,
    formatCurrency,
  };
}
