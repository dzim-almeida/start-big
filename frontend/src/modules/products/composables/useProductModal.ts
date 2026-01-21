import { ref } from 'vue';

const isModalOpen = ref<boolean>(false);

export function useProductModal() {
  const openModal = () => {
    isModalOpen.value = true;
  };

  const closeModal = () => {
    isModalOpen.value = false;
  };

  return {
    isModalOpen,
    openModal,
    closeModal,
  };
}
