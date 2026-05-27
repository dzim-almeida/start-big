import { ref } from 'vue'
import { refDebounced } from '@vueuse/core'

import { useCustomersQuery } from '../queries/useCustomersQuery'
import { useCreateSaleMutation } from '../mutates/useCreateSaleMutation'

import { useCustomerModal } from '@/modules/customers/composables/modal/useCustomerModal'
import { useSaleModal } from './useSaleModal'
import { useAuthStore } from '@/shared/stores/auth.store'

type ModalMode = 'create' | 'change'

const customerModalIsOpen = ref(false)
const modalMode = ref<ModalMode>('create')
let changeCallback: ((clienteId: number | null) => void) | null = null

export function useCustomerSearchModal() {
  const searchTerm = ref('')
  const debouncedSearchTerm = refDebounced(searchTerm, 500)

  const { openCreateModalWithCallback } = useCustomerModal()
  const { openSaleEditModal } = useSaleModal()
  const authStore = useAuthStore()

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
    modalMode.value = 'create'
    changeCallback = null
    customerModalIsOpen.value = true
  }

  function openCustomerModalForChange(callback: (clienteId: number | null) => void) {
    resetSearch()
    modalMode.value = 'change'
    changeCallback = callback
    customerModalIsOpen.value = true
  }

  function closeCustomerModal() {
    resetSearch()
    customerModalIsOpen.value = false
    changeCallback = null
  }

  function selectCustomer(customerId: number | null) {
    if (modalMode.value === 'change') {
      changeCallback?.(customerId)
      closeCustomerModal()
      return
    }

    createSaleMutation.mutate(
      {
        cliente_id: customerId,
        funcionario_id: authStore.userData?.funcionario_id ?? 1,
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
    const currentMode = modalMode.value
    const currentCallback = changeCallback
    closeCustomerModal()

    openCreateModalWithCallback((customer) => {
      if (currentMode === 'change') {
        currentCallback?.(customer.id)
      } else {
        selectCustomer(customer.id)
      }
    })
  }

  return {
    searchTerm,
    customers,

    customerModalIsOpen,
    modalMode,

    isSearchingCustomers,
    isCreatingSale: createSaleMutation.isPending,

    openCustomerModal,
    openCustomerModalForChange,
    closeCustomerModal,
    openCreateCustomerModal,
    selectCustomer,
  }
}