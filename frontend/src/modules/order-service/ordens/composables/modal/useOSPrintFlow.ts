import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';

export type { PrintFormat } from '@/shared/components/print/print.types';

interface UseOSPrintFlowParams {
  onClose: () => void;
}

export function useOSPrintFlow({ onClose }: UseOSPrintFlowParams) {
  const {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    openPrintSelect,
    handlePrintFormatSelected,
    closePrintSelectModal,
  } = usePrintFlow<'ENTRADA' | 'SAIDA'>();

  const isFinalizarModalOpen = ref(false);

  function printEntrada() {
    openPrintSelect('ENTRADA');
  }

  function printSaida() {
    openPrintSelect('SAIDA');
  }

  function printEntradaAndClose() {
    openPrintSelect('ENTRADA', () => onClose());
  }

  function handleFinalizarOS() {
    isFinalizarModalOpen.value = true;
  }

  function closeFinalizarModal() {
    isFinalizarModalOpen.value = false;
  }

  function onFinalized(payload: { shouldPrint: boolean }) {
    isFinalizarModalOpen.value = false;

    if (payload.shouldPrint) {
      openPrintSelect('SAIDA', () => onClose());
    } else {
      onClose();
    }
  }

  return {
    printType,
    printFormat,
    isFinalizarModalOpen,
    isPrintSelectModalOpen,
    printEntrada,
    printSaida,
    printEntradaAndClose,
    handleFinalizarOS,
    closeFinalizarModal,
    onFinalized,
    handlePrintFormatSelected,
    closePrintSelectModal,
  };
}
