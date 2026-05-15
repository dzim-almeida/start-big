import { ref, computed } from 'vue';

import { ProductSaleRead } from '../../schemas/productSale.schema';

type ModalMode = 'create' | 'edit';

const itemModalIsOpen = ref(false);
const itemModalMode = ref<ModalMode>('edit');
const selectedItem = ref<ProductSaleRead | null>(null);

export function useItemModal() {
  const isCreateMode = computed(() => itemModalMode.value === 'create');

  const isEditMode = computed(() => itemModalMode.value === 'edit');

  function closeItemModal() {
    itemModalIsOpen.value = false;
    itemModalMode.value = 'edit';
  }

  function openCreateItemModal() {
    itemModalIsOpen.value = true;
    itemModalMode.value = 'create';
    selectedItem.value = null;
  }

  function openEditItemModal(item: ProductSaleRead) {
    selectedItem.value = item;
    itemModalIsOpen.value = true;
    itemModalMode.value = 'edit';
    console.log('openEditItemModal', item);
  }

  return {
    itemModalIsOpen,
    isCreateMode,
    isEditMode,
    selectedItem,
    closeItemModal,
    openCreateItemModal,
    openEditItemModal,
  };
}
