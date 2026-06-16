import { reactive, ref } from 'vue';

const isAddProductModalOpen = ref(false);

export function useAddProductModal() {
  return reactive({
    isAddProductModalOpen,
    openAddProductModal() {
      isAddProductModalOpen.value = true;
    },
    closeAddProductModal() {
      isAddProductModalOpen.value = false;
    },
  });
}
