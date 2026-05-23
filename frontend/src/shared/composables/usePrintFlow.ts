import { ref } from 'vue';
import type { PrintFormat } from '@/shared/components/print/print.types';

export function usePrintFlow<T extends string>() {
  const printType = ref<T>('' as T);
  const printFormat = ref<PrintFormat>('A4');
  const isPrintSelectModalOpen = ref(false);
  const pendingPrintAction = ref<(() => void) | null>(null);

  function openPrintSelect(type: T, afterPrint?: () => void) {
    printType.value = type as typeof printType.value;
    pendingPrintAction.value = afterPrint ?? null;
    isPrintSelectModalOpen.value = true;
  }

  function handlePrintFormatSelected(format: PrintFormat) {
    printFormat.value = format;
    isPrintSelectModalOpen.value = false;

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

  return {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    openPrintSelect,
    handlePrintFormatSelected,
    closePrintSelectModal,
  };
}
