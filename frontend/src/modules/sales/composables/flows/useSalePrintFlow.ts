import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';
import { useImpressao } from '@/shared/composables/useImpressao';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useCompanyPrintInfo, getPaymentDisplayName } from '@/shared/utils/print.utils';
import { usePaymentMethodsQuery } from '../queries/usePaymentMethodsQuery';
import { saleToEscPos } from '../../components/print/saleToEscPos';
import { saleService } from '../../api.service';
import type { SaleRead } from '../../schemas/sale.schema';

export type SalePrintType = 'VENDA';

export function useSalePrintFlow() {
  const {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    openPrintSelect,
    printDirect,
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

  const impressao = useImpressao();
  const impressaoStore = useImpressaoStore();
  const { companyInfo } = useCompanyPrintInfo();

  function vendaTemPagamentoDinheiro(sale: SaleRead): boolean {
    return (sale.pagamentos ?? []).some((pg) =>
      resolvePaymentMethodName(pg.forma_pagamento_id).toLowerCase().includes('dinheiro'),
    );
  }

  /**
   * Impressão pós-finalização da venda conforme a configuração local:
   * automático + cupom → ESC/POS silencioso na térmica;
   * automático + A4 → abre o diálogo do Windows direto com o recibo pronto;
   * perguntar → modal de formato; não imprimir → só executa o callback.
   * Falha no ESC/POS cai no modal de formato.
   */
  async function imprimirAposFinalizar(sale: SaleRead, afterPrint?: () => void) {
    const config = impressaoStore.config;

    if (config.auto_imprimir_venda === 'nao') {
      afterPrint?.();
      return;
    }

    if (config.auto_imprimir_venda === 'automatico') {
      if (config.formato_venda === 'a4') {
        saleForPrint.value = sale;
        printDirect('VENDA', 'A4', () => {
          saleForPrint.value = null;
          afterPrint?.();
        });
        return;
      }

      if (impressao.podeImprimirDireto.value) {
        const dados = saleToEscPos(sale, {
          bobina: config.bobina,
          empresa: companyInfo.value,
          resolverPagamento: resolvePaymentMethodName,
          abrirGaveta: config.gaveta_ativa && config.abrir_gaveta_na_venda && vendaTemPagamentoDinheiro(sale),
        });
        if (await impressao.imprimirCupom(dados)) {
          afterPrint?.();
          return;
        }
      }
    }

    printSaleData(sale, 'VENDA', afterPrint);
  }

  return {
    imprimirAposFinalizar,
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
