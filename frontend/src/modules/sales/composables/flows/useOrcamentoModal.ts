import { ref, computed } from 'vue';

import { useOrcamentoDraftQuery } from '../queries/useOrcamentoDraftQuery';

const orcamentoModalIsOpen = ref<boolean>(false);
const selectedOrcamentoId = ref<number | null>(null);

export function useOrcamentoModal() {
  const draftQuery = useOrcamentoDraftQuery(
    computed(() => (orcamentoModalIsOpen.value ? selectedOrcamentoId.value : null)),
  );

  const orcamento = computed(() => draftQuery.data.value);
  const isLoading = computed(() => draftQuery.isLoading.value);

  function openOrcamentoModal(orcamentoId: number) {
    selectedOrcamentoId.value = orcamentoId;
    orcamentoModalIsOpen.value = true;
  }

  function closeOrcamentoModal() {
    orcamentoModalIsOpen.value = false;
    selectedOrcamentoId.value = null;
  }

  return {
    orcamentoModalIsOpen,
    openOrcamentoModal,
    closeOrcamentoModal,
    orcamento,
    isLoading,
    selectedOrcamentoId,
  };
}
