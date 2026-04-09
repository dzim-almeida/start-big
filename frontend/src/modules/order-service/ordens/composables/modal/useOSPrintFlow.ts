import { ref } from 'vue';

export type PrintFormat = 'A4' | 'CUPOM';

interface UseOSPrintFlowParams {
  onClose: () => void;
}

export function useOSPrintFlow({ onClose }: UseOSPrintFlowParams) {
  const printType = ref<'ENTRADA' | 'SAIDA'>('ENTRADA');
  const printFormat = ref<PrintFormat>('A4');
  const isFinalizarModalOpen = ref(false);
  const isPrintSelectModalOpen = ref(false);

  // Guarda a ação pendente (executada após o usuário selecionar o formato)
  const pendingPrintAction = ref<(() => void) | null>(null);

  function openPrintSelect(type: 'ENTRADA' | 'SAIDA', afterPrint?: () => void) {
    printType.value = type;
    pendingPrintAction.value = afterPrint ?? null;
    isPrintSelectModalOpen.value = true;
  }

  function handlePrintFormatSelected(format: PrintFormat) {
    printFormat.value = format;
    isPrintSelectModalOpen.value = false;

    // Aguarda o próximo tick para o template correto ser renderizado via v-if
    setTimeout(() => {
      window.print();
      pendingPrintAction.value?.();
      pendingPrintAction.value = null;
    }, 100);
  }

  function closePrintSelectModal() {
    isPrintSelectModalOpen.value = false;
    pendingPrintAction.value = null;
  }

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
