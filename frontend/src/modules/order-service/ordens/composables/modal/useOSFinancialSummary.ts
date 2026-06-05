import { computed, type ComputedRef, type Ref } from 'vue';

import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import type { OsItemCreateSchemaDataType } from '../../schemas/relationship/osItem.schema';

interface UseOSFinancialSummaryParams {
  isCreateMode: ComputedRef<boolean>;
  createItems: ComputedRef<OsItemCreateSchemaDataType[]>;
  currentOSData: ComputedRef<OrderServiceReadDataType | null>;
  createDesconto: Ref<number | undefined>;
  createValorEntrada: Ref<number | undefined>;
  updateValorEntrada: Ref<number | undefined>;
  updateTaxaEntrega: Ref<number | undefined>;
}

export function useOSFinancialSummary({
  isCreateMode,
  createItems,
  currentOSData,
  createDesconto,
  createValorEntrada,
  updateValorEntrada,
  updateTaxaEntrega,
}: UseOSFinancialSummaryParams) {
  const displaySubtotal = computed(() => {
    if (isCreateMode.value) {
      return createItems.value.reduce(
        (sum, item) => sum + item.quantidade * item.valor_unitario,
        0,
      );
    }
    return (currentOSData.value?.itens ?? []).reduce((sum, item) => sum + item.valor_total, 0);
  });

  const displayValorEntrega = computed(() =>
    updateTaxaEntrega.value ?? currentOSData.value?.taxa_entrega ?? 0
  );

  function handleValorEntregaUpdate(value: number) {
    if (!isCreateMode.value) updateTaxaEntrega.value = value;
  }

  const displayValorDesconto = computed(() => {
    if (isCreateMode.value) return createDesconto.value ?? 0;
    return currentOSData.value?.desconto ?? 0;
  });

  const displayValorTotal = computed(() => {
    if (isCreateMode.value) {
      return Math.max(0, displaySubtotal.value - displayValorDesconto.value);
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

  const displayValorAcrescimo = computed(() => currentOSData.value?.acrescimo ?? 0);

  return {
    displaySubtotal,
    displayValorEntrega,
    displayValorDesconto,
    displayValorTotal,
    displayValorEntrada,
    displayValorAcrescimo,
    handleValorEntradaUpdate,
    handleValorEntregaUpdate,
  };
}
