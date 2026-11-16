import { ref } from 'vue';
import { usePrintFlow } from '@/shared/composables/usePrintFlow';
import { useImpressao } from '@/shared/composables/useImpressao';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useCupomOS } from './useCupomOS';
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
  } = usePrintFlow<'ENTRADA' | 'SAIDA'>((tipo) =>
    tipo === 'ENTRADA' ? 'os_entrada' : 'os_entrega',
  );

  const isFinalizarModalOpen = ref(false);

  const impressao = useImpressao();
  const impressaoStore = useImpressaoStore();
  // Um montador só para o cupom do formulário e o da tabela (ver useCupomOS).
  const { montarCupom } = useCupomOS();

  /** Manda o cupom térmico direto pra impressora configurada; false = sem impressora/falhou */
  async function imprimirEscPosDireto(tipo: 'ENTRADA' | 'SAIDA'): Promise<boolean> {
    if (!impressao.podeImprimirDireto.value) return false;
    const os = getOS?.();
    if (!os) return false;
    return impressao.imprimirCupom(await montarCupom(os, tipo));
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

  /**
   * Regra única de impressão (sem perguntar formato), obedecendo `formato_os`:
   * - Formato Cupom + térmica configurada → ESC/POS direto (silencioso).
   * - Formato A4 → recibo A4 abrindo o diálogo do sistema, SEM tentar ESC/POS.
   * - Sem térmica (ou falha no envio) → cai no A4.
   *
   * O teste do formato existe porque ESC/POS sao bytes de comando, nao texto:
   * despejados numa impressora comum, saem como uma folha de pontinhos. Antes
   * daqui o ramo ESC/POS era tentado SEMPRE que houvesse impressora, e escolher
   * A4 na tela nao tinha efeito nenhum — o `formato_os` era gravado e nunca lido.
   */
  async function imprimir(tipo: 'ENTRADA' | 'SAIDA', afterPrint?: () => void) {
    if (impressaoStore.config.formato_os === 'cupom' && (await imprimirEscPosDireto(tipo))) {
      afterPrint?.();
      return;
    }
    printDirect(tipo, 'A4', afterPrint);
  }

  function printEntrada() {
    imprimir('ENTRADA');
  }

  function printSaida() {
    imprimir('SAIDA');
  }

  /**
   * Impressão pós-criação/finalização, conforme `auto_imprimir_os`:
   * 'perguntar' → o atendente escolhe o formato nesta OS;
   * 'automatico' → segue a regra única (o formato configurado).
   * O 'nao' é filtrado antes, por quem chama.
   */
  async function imprimirAutomaticoEFechar(tipo: 'ENTRADA' | 'SAIDA') {
    if (impressaoStore.config.auto_imprimir_os === 'perguntar') {
      openPrintSelect(tipo, () => onClose());
      return;
    }
    await imprimir(tipo, () => onClose());
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
