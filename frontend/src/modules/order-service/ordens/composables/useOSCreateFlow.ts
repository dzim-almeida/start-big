import { ref } from 'vue';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../schemas/relationship/customer/customer.schema';

// =============================================
// Shared State (singleton pattern)
// =============================================

const isClienteSearchOpen = ref(false);
const isFormModalOpen = ref(false);
const selectedCliente = ref<CustomerUnionReadSchemaDataType | null>(null);
const selectedOS = ref<OrderServiceReadDataType | null>(null);

// =============================================
// Composable
// =============================================

export function useOSCreateFlow() {
  function openNovaOS() {
    selectedOS.value = null;
    selectedCliente.value = null;
    isClienteSearchOpen.value = true;
  }

  function openExistingOS(os: OrderServiceReadDataType) {
    selectedOS.value = os;
    selectedCliente.value = null;
    isFormModalOpen.value = true;
  }

  function handleClienteSelected(cliente: CustomerUnionReadSchemaDataType) {
    selectedCliente.value = cliente;
    isClienteSearchOpen.value = false;
    isFormModalOpen.value = true;
  }

  function handleChangeCliente() {
    isFormModalOpen.value = false;
    isClienteSearchOpen.value = true;
  }

  function closeClienteSearch() {
    isClienteSearchOpen.value = false;
  }

  function closeFormModal() {
    isFormModalOpen.value = false;
    selectedOS.value = null;
    selectedCliente.value = null;
  }

  return {
    isClienteSearchOpen,
    isFormModalOpen,
    selectedCliente,
    selectedOS,
    openNovaOS,
    openExistingOS,
    handleClienteSelected,
    handleChangeCliente,
    closeClienteSearch,
    closeFormModal,
  };
}
