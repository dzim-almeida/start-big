import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';
import { getPaymentDisplayName } from '@/shared/utils/print.utils';
import { usePaymentMethodsQuery } from '../queries/usePaymentMethodsQuery';
import { saleService } from '../../api.service';
import type { SaleRead } from '../../schemas/sale.schema';

export type SalePrintType = 'ORCAMENTO' | 'VENDA';

export function useSalePrintFlow() {
  const {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    openPrintSelect,
    handlePrintFormatSelected,
    closePrintSelectModal,
  } = usePrintFlow<SalePrintType>();

  const saleForPrint = ref<SaleRead | null>(null);
  const { formasPagamento } = usePaymentMethodsQuery();

  function resolvePaymentMethodName(formaId: number): string {
    const method = formasPagamento.value.find((fp) => fp.id === formaId);
    return getPaymentDisplayName(method?.nome ?? 'Desconhecido');
  }

  async function printSale(saleId: number, type: SalePrintType, afterPrint?: () => void) {
    const sale = await saleService.getSale(saleId);
    saleForPrint.value = sale;
    openPrintSelect(type, () => {
      saleForPrint.value = null;
      afterPrint?.();
    });
  }

  function printSaleData(sale: SaleRead, type: SalePrintType, afterPrint?: () => void) {
    saleForPrint.value = sale;
    openPrintSelect(type, () => {
      saleForPrint.value = null;
      afterPrint?.();
    });
  }

  return {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    saleForPrint,
    printSale,
    printSaleData,
    handlePrintFormatSelected,
    closePrintSelectModal,
    resolvePaymentMethodName,
  };
}
