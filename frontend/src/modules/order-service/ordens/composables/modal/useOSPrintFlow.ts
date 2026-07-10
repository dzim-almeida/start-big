import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';
import { useImpressao } from '@/shared/composables/useImpressao';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import { osToEscPos } from '../../components/osToEscPos';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import type { PrintFormat } from '@/shared/components/print/print.types';

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
    printDirect,
    handlePrintFormatSelected: handlePrintFormatSelectedBase,
    closePrintSelectModal,
  } = usePrintFlow<'ENTRADA' | 'SAIDA'>();

  const isFinalizarModalOpen = ref(false);

  const impressao = useImpressao();
  const impressaoStore = useImpressaoStore();
  const { companyInfo } = useCompanyPrintInfo();

  /** Manda o cupom térmico direto pra impressora configurada; false = sem impressora/falhou */
  async function imprimirEscPosDireto(tipo: 'ENTRADA' | 'SAIDA'): Promise<boolean> {
    if (!impressao.podeImprimirDireto.value) return false;
    const os = getOS?.();
    if (!os) return false;
    const dados = osToEscPos(os, tipo, {
      bobina: impressaoStore.config.bobina,
      empresa: companyInfo.value,
    });
    return impressao.imprimirCupom(dados);
  }

  /** Tenta o cupom térmico direto conforme a config local; false = usar o modal */
  async function tentarImpressaoDireta(tipo: 'ENTRADA' | 'SAIDA'): Promise<boolean> {
    if (impressaoStore.config.auto_imprimir_os !== 'automatico') return false;
    return imprimirEscPosDireto(tipo);
  }

  /**
   * Formato escolhido no modal de reimpressão manual: Cupom Térmico sai direto
   * pela impressora (sem diálogo); A4 continua abrindo o diálogo de impressão
   * do sistema, onde o usuário escolhe a impressora/PDF.
   */
  async function handlePrintFormatSelected(format: PrintFormat) {
    if (format === 'CUPOM' && (await imprimirEscPosDireto(printType.value))) {
      closePrintSelectModal();
      printFormat.value = '' as PrintFormat;
      return;
    }
    handlePrintFormatSelectedBase(format);
  }

  function printEntrada() {
    openPrintSelect('ENTRADA');
  }

  function printSaida() {
    openPrintSelect('SAIDA');
  }

  /** Imprime conforme a config (A4 direto, cupom silencioso ou modal) e fecha */
  async function imprimirAutomaticoEFechar(tipo: 'ENTRADA' | 'SAIDA') {
    if (impressaoStore.config.auto_imprimir_os === 'automatico' && impressaoStore.config.formato_os === 'a4') {
      printDirect(tipo, 'A4', () => onClose());
      return;
    }
    if (await tentarImpressaoDireta(tipo)) {
      onClose();
      return;
    }
    openPrintSelect(tipo, () => onClose());
  }

  async function printEntradaAndClose() {
    // 'nao' vale só para a impressão automática pós-criação;
    // a reimpressão manual (printEntrada) continua disponível
    if (impressaoStore.config.auto_imprimir_os === 'nao') {
      onClose();
      return;
    }
    await imprimirAutomaticoEFechar('ENTRADA');
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
    await imprimirAutomaticoEFechar('SAIDA');
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
