import { ref } from 'vue';
import { refDebounced } from '@vueuse/core';

import { useCustomersQuery } from './queries/useCustomersQuery';
import { useCreateSaleMutation } from './mutates/useCreateSaleMutation';

import { useCustomerModal } from '@/modules/customers/composables/modal/useCustomerModal';

const customerModalIsOpen = ref<boolean>(false);

export function useCustomerSearchModal() {

  const { openCreateModalWithCallback } = useCustomerModal();

  function openCreateCustomerModal() {
    openCreateModalWithCallback((customer) => {
      createSale(customer.id);
    });
    closeCustomerModal();
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

  const createSaleMutation = useCreateSaleMutation();

  function createSale(customerId: number | null) {
    createSaleMutation.mutate({
      cliente_id: customerId,
      funcionario_id: 1,
    });
    closeCustomerModal();
  }

  return {
    searchTerm,
    isLoading,
    customers,
    customerModalIsOpen,
    openCustomerModal,
    closeCustomerModal,
    openCreateCustomerModal,
    createSale,
  };
}
