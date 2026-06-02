import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';
import { orcamentoService } from '../../orcamento.service';
import type { OrcamentoRead } from '../../schemas/orcamento.schema';

export type OrcamentoPrintType = 'ORCAMENTO';

export function useOrcamentoPrintFlow() {
  const {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    openPrintSelect,
    handlePrintFormatSelected,
    closePrintSelectModal,
  } = usePrintFlow<OrcamentoPrintType>();

  const orcamentoForPrint = ref<OrcamentoRead | null>(null);

  async function printOrcamento(orcamentoId: number, afterPrint?: () => void) {
    const orc = await orcamentoService.getOrcamento(orcamentoId);
    orcamentoForPrint.value = orc;
    openPrintSelect('ORCAMENTO', () => {
      orcamentoForPrint.value = null;
      afterPrint?.();
    });
  }

  return {
    printType,
    printFormat,
    isPrintSelectModalOpen: isPrintSelectModalOpen,
    orcamentoForPrint,
    printOrcamento,
    handlePrintFormatSelected,
    closePrintSelectModal,
  };
}
