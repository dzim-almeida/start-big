import { ref, computed } from 'vue';

import { useSaleDraftQuery } from '../queries/useSaleDraftQuery';
import { useSaleDetailQuery } from '../queries/useSaleDetailQuery';

type SaleModalMode = 'view' | 'edit';

const saleModalIsOpen = ref<boolean>(false);
const selectedSaleId = ref<number | null>(null);
const modalMode = ref<SaleModalMode>('view');

export function useSaleModal() {
  const isEditMode = computed(() => modalMode.value === 'edit');
  const isViewMode = computed(() => modalMode.value === 'view');

  const draftQuery = useSaleDraftQuery(
    computed(() => (isEditMode.value ? selectedSaleId.value : null)),
  );

  const detailQuery = useSaleDetailQuery(
    computed(() => (isViewMode.value ? selectedSaleId.value : null)),
  );

  const sale = computed(() => (isEditMode.value ? draftQuery.data.value : detailQuery.data.value));

  const isLoading = computed(() =>
    isEditMode.value ? draftQuery.isLoading.value : detailQuery.isLoading.value,
  );

  function openSaleEditModal(saleId: number) {
    selectedSaleId.value = saleId;
    modalMode.value = 'edit';
    saleModalIsOpen.value = true;
  }

  function openSaleViewModal(saleId: number) {
    selectedSaleId.value = saleId;
    modalMode.value = 'view';
    saleModalIsOpen.value = true;
  }

  function closeSaleModal() {
    saleModalIsOpen.value = false;
    selectedSaleId.value = null;
    modalMode.value = 'view';
  }

  return {
    saleModalIsOpen,
    openSaleEditModal,
    openSaleViewModal,
    closeSaleModal,
    sale,
    isLoading,
    selectedSaleId,
    isEditMode,
    isViewMode
  };
}
