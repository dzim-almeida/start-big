import { ref } from 'vue';

interface ConfirmModalState {
  title: string;
  message: string;
  highlightText?: string;
  variant: 'primary' | 'danger';
  label: string;
  action: () => void;
}

const confirmModalIsOpen = ref(false);
const confirmModalState = ref<ConfirmModalState>({
  title: '',
  message: '',
  highlightText: undefined,
  variant: 'primary',
  label: 'Confirmar',
  action: () => {},
});
const confirmModalPending = ref(false);

export function useConfirmSaleAction() {
  function openConfirmModal(opts: ConfirmModalState) {
    confirmModalState.value = opts;
    confirmModalPending.value = false;
    confirmModalIsOpen.value = true;
  }

  function closeConfirmModal() {
    confirmModalIsOpen.value = false;
    confirmModalPending.value = false;
  }

  function handleConfirm() {
    confirmModalState.value.action();
  }

  return {
    confirmModalIsOpen,
    confirmModalState,
    confirmModalPending,
    openConfirmModal,
    closeConfirmModal,
    handleConfirm,
  };
}
