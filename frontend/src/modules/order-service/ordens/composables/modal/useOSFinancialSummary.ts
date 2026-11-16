import { computed, type ComputedRef, type Ref } from 'vue';

import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import type { OsItemCreateSchemaDataType } from '../../schemas/relationship/osItem.schema';
import { itemContaNoTotal, somarItensDaOS } from '../../../shared/utils/formatters';

interface UseOSFinancialSummaryParams {
  isCreateMode: ComputedRef<boolean>;
  createItems: ComputedRef<OsItemCreateSchemaDataType[]>;
  currentOSData: ComputedRef<OrderServiceReadDataType | null>;
  createDesconto: Ref<number | null | undefined>;
  createValorEntrada: Ref<number | null | undefined>;
  updateValorEntrada: Ref<number | null | undefined>;
  createFormaPagamentoEntrada: Ref<number | null | undefined>;
  updateFormaPagamentoEntrada: Ref<number | null | undefined>;
  createTaxaEntrega: Ref<number | null | undefined>;
  updateTaxaEntrega: Ref<number | null | undefined>;
}

export function useOSFinancialSummary({
  isCreateMode,
  createItems,
  currentOSData,
  createDesconto,
  createValorEntrada,
  updateValorEntrada,
  createFormaPagamentoEntrada,
  updateFormaPagamentoEntrada,
  createTaxaEntrega,
  updateTaxaEntrega,
}: UseOSFinancialSummaryParams) {
  // Item REPROVADO fora da soma — regra única em `itemContaNoTotal`, que espelha
  // o `_item_conta_no_total` do backend. Na OS ainda não salva o valor da linha
  // não existe pronto, por isso aqui o cálculo é quantidade × unitário.
  const displaySubtotal = computed(() => {
    if (isCreateMode.value) {
      return createItems.value
        .filter(itemContaNoTotal)
        .reduce((sum, item) => sum + item.quantidade * item.valor_unitario, 0);
    }
    return somarItensDaOS(currentOSData.value?.itens);
  });

  const displayValorEntrega = computed(() => {
    if (isCreateMode.value) return createTaxaEntrega.value ?? 0;
    return updateTaxaEntrega.value ?? currentOSData.value?.taxa_entrega ?? 0;
  });

  // Na OS nova o valor ia para lugar nenhum (só a edição gravava): o campo
  // aparecia, aceitava o número e o total não mudava.
  function handleValorEntregaUpdate(value: number) {
    if (isCreateMode.value) {
      createTaxaEntrega.value = value;
      return;
    }
    updateTaxaEntrega.value = value;
  }

  const displayValorDesconto = computed(() => {
    if (isCreateMode.value) return createDesconto.value ?? 0;
    return currentOSData.value?.desconto ?? 0;
  });

  const displayValorTotal = computed(() => {
    if (isCreateMode.value) {
      // Mesma fórmula do backend na criação: itens − desconto + deslocamento.
      return Math.max(0, displaySubtotal.value - displayValorDesconto.value + displayValorEntrega.value);
    }
    const dbTotal = currentOSData.value?.valor_total ?? 0;
    if (updateTaxaEntrega.value !== undefined && updateTaxaEntrega.value !== null) {
      const dbEntrega = currentOSData.value?.taxa_entrega ?? 0;
      return Math.max(0, dbTotal - dbEntrega + updateTaxaEntrega.value);
    }
    return dbTotal;
  });

  const displayValorEntrada = computed(() => {
    if (isCreateMode.value) return createValorEntrada.value ?? 0;
    return updateValorEntrada.value ?? currentOSData.value?.valor_entrada ?? 0;
  });

  function handleValorEntradaUpdate(value: number) {
    if (isCreateMode.value) {
      createValorEntrada.value = value;
      return;
    }
    updateValorEntrada.value = value;
  }

  // Forma de pagamento do adiantamento. `null` (não informado) é estado válido:
  // é o de toda OS aberta antes deste campo existir.
  const displayFormaPagamentoEntradaId = computed<number | null>(() => {
    if (isCreateMode.value) return createFormaPagamentoEntrada.value ?? null;
    return (
      updateFormaPagamentoEntrada.value ??
      currentOSData.value?.forma_pagamento_entrada?.id ??
      null
    );
  });

  function handleFormaPagamentoEntradaUpdate(value: number | null) {
    if (isCreateMode.value) {
      createFormaPagamentoEntrada.value = value;
      return;
    }
    updateFormaPagamentoEntrada.value = value;
  }

  const displayValorAcrescimo = computed(() => currentOSData.value?.acrescimo ?? 0);

  return {
    displaySubtotal,
    displayValorEntrega,
    displayValorDesconto,
    displayValorTotal,
    displayValorEntrada,
    displayValorAcrescimo,
    displayFormaPagamentoEntradaId,
    handleValorEntradaUpdate,
    handleValorEntregaUpdate,
    handleFormaPagamentoEntradaUpdate,
  };
}
