import { ref } from 'vue'
import { refDebounced } from '@vueuse/core'

import { useCustomersQuery } from '../queries/useCustomersQuery'
import { useCreateSaleMutation } from '../mutates/useCreateSaleMutation'

import { useCustomerModal } from '@/modules/customers/composables/modal/useCustomerModal'
import { useSaleModal } from './useSaleModal'

const customerModalIsOpen = ref(false)

export function useCustomerSearchModal() {
  const searchTerm = ref('')
  const debouncedSearchTerm = refDebounced(searchTerm, 500)

  const { openCreateModalWithCallback } = useCustomerModal()
  const { openSaleEditModal } = useSaleModal()

  const {
    data: customers,
    isLoading: isSearchingCustomers,
  } = useCustomersQuery(debouncedSearchTerm)

  const createSaleMutation = useCreateSaleMutation()

  function resetSearch() {
    searchTerm.value = ''
  }

  function openCustomerModal() {
    resetSearch()
    customerModalIsOpen.value = true
  }

  function closeCustomerModal() {
    resetSearch()
    customerModalIsOpen.value = false
  }

  function createSale(customerId: number | null) {
    createSaleMutation.mutate(
      {
        cliente_id: customerId,
        funcionario_id: 1,
      },
      {
        onSuccess: (createdSale) => {
          closeCustomerModal()
          openSaleEditModal(createdSale.id)
        },
      },
    )
  }

  function openCreateCustomerModal() {
    closeCustomerModal()

    openCreateModalWithCallback((customer) => {
      createSale(customer.id)
    })
  }

  return {
    searchTerm,
    customers,

    customerModalIsOpen,

    isSearchingCustomers,
    isCreatingSale: createSaleMutation.isPending,

    openCustomerModal,
    closeCustomerModal,
    openCreateCustomerModal,
    createSale,
  }
}