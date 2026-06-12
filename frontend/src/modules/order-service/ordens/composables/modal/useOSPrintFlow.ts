import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';
import { useImpressao } from '@/shared/composables/useImpressao';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import { osToEscPos } from '../../components/osToEscPos';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';

export type { PrintFormat } from '@/shared/components/print/print.types';

interface UseOSPrintFlowParams {
  onClose: () => void;
  /** Getter da OS atual, usado na impressão térmica direta (ESC/POS) */
  getOS?: () => OrderServiceReadDataType | null;
}

export function useOSPrintFlow({ onClose, getOS }: UseOSPrintFlowParams) {
  const {
    printType,
    printFormat,
    isPrintSelectModalOpen,
    openPrintSelect,
    handlePrintFormatSelected,
    closePrintSelectModal,
  } = usePrintFlow<'ENTRADA' | 'SAIDA'>();

  const isFinalizarModalOpen = ref(false);

  const impressao = useImpressao();
  const impressaoStore = useImpressaoStore();
  const { companyInfo } = useCompanyPrintInfo();

  /** Tenta o cupom térmico direto conforme a config local; false = usar o modal */
  async function tentarImpressaoDireta(tipo: 'ENTRADA' | 'SAIDA'): Promise<boolean> {
    if (impressaoStore.config.auto_imprimir_os !== 'automatico') return false;
    if (!impressao.podeImprimirDireto.value) return false;
    const os = getOS?.();
    if (!os) return false;
    const dados = osToEscPos(os, tipo, {
      bobina: impressaoStore.config.bobina,
      empresa: companyInfo.value,
    });
    return impressao.imprimirCupom(dados);
  }

  function printEntrada() {
    openPrintSelect('ENTRADA');
  }

  function printSaida() {
    openPrintSelect('SAIDA');
  }

  async function printEntradaAndClose() {
    // 'nao' vale só para a impressão automática pós-criação;
    // a reimpressão manual (printEntrada) continua disponível
    if (impressaoStore.config.auto_imprimir_os === 'nao') {
      onClose();
      return;
    }
    if (await tentarImpressaoDireta('ENTRADA')) {
      onClose();
      return;
    }
    openPrintSelect('ENTRADA', () => onClose());
  }

  function handleFinalizarOS() {
    isFinalizarModalOpen.value = true;
  }

  function closeFinalizarModal() {
    isFinalizarModalOpen.value = false;
  }

  async function onFinalized(payload: { shouldPrint: boolean }) {
    isFinalizarModalOpen.value = false;

    if (!payload.shouldPrint) {
      onClose();
      return;
    }
    if (await tentarImpressaoDireta('SAIDA')) {
      onClose();
      return;
    }
    openPrintSelect('SAIDA', () => onClose());
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
