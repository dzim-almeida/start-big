import { ref } from 'vue';
import { refDebounced } from '@vueuse/core';

import { useCustomersQuery } from './queries/useCustomersQuery';

import { useCustomerModal } from '@/modules/customers/composables/modal/useCustomerModal';

const customerModalIsOpen = ref<boolean>(false);

export function useCustomerSearchModal() {
  const { openCreateModalWithCallback } = useCustomerModal();

  function openCreateCustomerModal() {
    openCreateModalWithCallback((customer) => {
      searchTerm.value = '';
      console.log('Cliente criado: ', customer);
    });
  }

  function openCustomerModal() {
    searchTerm.value = '';
    customerModalIsOpen.value = true;
  }

  function closeCustomerModal() {
    searchTerm.value = '';
    customerModalIsOpen.value = false;
  }

  const searchTerm = ref<string | null>(null);
  const debouncedSearchTerm = refDebounced(searchTerm, 500);

  const { data: customers, isLoading } = useCustomersQuery(debouncedSearchTerm);

  return {
    searchTerm,
    isLoading,
    customers,
    customerModalIsOpen,
    openCustomerModal,
    closeCustomerModal,
    openCreateCustomerModal,
  };
}
