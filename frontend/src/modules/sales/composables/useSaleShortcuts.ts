import { type Ref } from 'vue';
import { useMagicKeys, whenever, useEventListener } from '@vueuse/core';

interface SaleShortcutsContext {
  saleModalIsOpen: Ref<boolean>;
  isEditMode: Ref<boolean>;
  finishModalIsOpen: Ref<boolean>;
  itemModalIsOpen: Ref<boolean>;
  addPaymentModalIsOpen: Ref<boolean>;
  onCreateSale: () => void;
  onOpenFinishModal: () => void;
  onOpenItemModal: () => void;
  onOpenAddPaymentModal: () => void;
  onCancelSale: () => void;
  onCloseSaleModal: () => void;
  onCloseFinishModal: () => void;
  onCloseItemModal: () => void;
  onCloseAddPaymentModal: () => void;
  onFocusSearch: () => void;
}

export function useSaleShortcuts(context: SaleShortcutsContext) {
  const keys = useMagicKeys();

  // Prevenir Ctrl+F padrão do browser quando o modal está aberto
  useEventListener(document, 'keydown', (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'f' && context.saleModalIsOpen.value && context.isEditMode.value) {
      e.preventDefault();
    }
  });

  // F2 — Criar nova venda (apenas quando o modal de venda NÃO está aberto)
  whenever(keys.F2, () => {
    if (!context.saleModalIsOpen.value) {
      context.onCreateSale();
    }
  });

  // F4 — Abrir modal de produto avulso (dentro do SaleModal em modo edição)
  whenever(keys.F4, () => {
    if (context.saleModalIsOpen.value && context.isEditMode.value && !context.finishModalIsOpen.value) {
      context.onOpenItemModal();
    }
  });

  // F6 — Abrir modal de adicionar pagamento (dentro do FinishSaleModal)
  whenever(keys.F6, () => {
    if (context.finishModalIsOpen.value && !context.addPaymentModalIsOpen.value) {
      context.onOpenAddPaymentModal();
    }
  });

  // Ctrl+F — Focar busca de produtos
  whenever(keys.Ctrl_F, () => {
    if (context.saleModalIsOpen.value && context.isEditMode.value && !context.finishModalIsOpen.value && !context.itemModalIsOpen.value) {
      context.onFocusSearch();
    }
  });

  // Ctrl+Enter — Abrir modal de finalização
  whenever(keys.Ctrl_Enter, () => {
    if (context.saleModalIsOpen.value && context.isEditMode.value && !context.finishModalIsOpen.value && !context.itemModalIsOpen.value) {
      context.onOpenFinishModal();
    }
  });

  // Ctrl+Backspace — Cancelar venda
  whenever(keys.Ctrl_Backspace, () => {
    if (context.saleModalIsOpen.value && context.isEditMode.value && !context.finishModalIsOpen.value && !context.itemModalIsOpen.value) {
      context.onCancelSale();
    }
  });

  // Escape — Fechar modal atual (respeita hierarquia)
  whenever(keys.Escape, () => {
    if (context.addPaymentModalIsOpen.value) {
      context.onCloseAddPaymentModal();
      return;
    }
    if (context.finishModalIsOpen.value) {
      context.onCloseFinishModal();
      return;
    }
    if (context.itemModalIsOpen.value) {
      context.onCloseItemModal();
      return;
    }
    if (context.saleModalIsOpen.value) {
      context.onCloseSaleModal();
    }
  });
}
