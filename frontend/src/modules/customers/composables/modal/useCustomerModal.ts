/**
 * @fileoverview Gerenciamento de estado do modal de clientes (singleton)
 * @description Usa refs de nível de módulo para compartilhar estado entre componentes.
 * Pode ser chamado de qualquer módulo do sistema.
 */

import { ref, computed } from 'vue';
import { CustomerUnionReadSchemaDataType, isCustomerPF } from '@/shared/schemas/customer/customer.schema';

// =============================================
// Types
// =============================================

export type ModalMode = 'create' | 'edit' | 'view';

// =============================================
// Types
// =============================================

type CustomerCallback = ((customer: CustomerUnionReadSchemaDataType) => void) | null;

// =============================================
// Shared State (singleton)
// =============================================

const isOpen = ref(false);
const mode = ref<ModalMode>('create');
const selectedCustomer = ref<CustomerUnionReadSchemaDataType | null>(null);
const onCreatedCallback = ref<CustomerCallback>(null);
const onUpdatedCallback = ref<CustomerCallback>(null);

// =============================================
// Composable
// =============================================

export function useCustomerModal() {

  function openCreateModal() {
    selectedCustomer.value = null;
    mode.value = 'create';
    isOpen.value = true;
  }

  function openEditModal(customer: CustomerUnionReadSchemaDataType) {
    selectedCustomer.value = customer;
    mode.value = 'edit';
    isOpen.value = true;
  }

  function openCreateModalWithCallback(callback: (customer: CustomerUnionReadSchemaDataType) => void) {
    onCreatedCallback.value = callback;
    openCreateModal();
  }

  function openEditModalWithCallback(
    customer: CustomerUnionReadSchemaDataType,
    callback: (customer: CustomerUnionReadSchemaDataType) => void,
  ) {
    onUpdatedCallback.value = callback;
    openEditModal(customer);
  }

  function openViewModal(customer: CustomerUnionReadSchemaDataType) {
    selectedCustomer.value = customer;
    mode.value = 'view';
    isOpen.value = true;
  }

  function closeModal() {
    isOpen.value = false;
    setTimeout(() => {
      selectedCustomer.value = null;
      mode.value = 'create';
      onCreatedCallback.value = null;
      onUpdatedCallback.value = null;
    }, 300);
  }

  const isCreateMode = computed(() => mode.value === 'create');
  const isEditMode = computed(() => mode.value === 'edit');
  const isViewMode = computed(() => mode.value === 'view');

  const modalTitle = computed(() => {
    if (!isCreateMode.value && selectedCustomer.value) {
      const customerType = selectedCustomer.value.tipo;
      if (mode.value === 'edit') {
        return customerType === 'PF' ? 'Editar Cliente PF' : 'Editar Cliente PJ';
      }
      return customerType === 'PF' ? 'Detalhes do Cliente PF' : 'Detalhes do Cliente PJ';
    }
    return 'Novo Cliente';
  });

  const modalSubtitle = computed(() => {
    if (selectedCustomer.value) {
      if (isCustomerPF(selectedCustomer.value)) {
        return selectedCustomer.value.nome;
      }
      return selectedCustomer.value.nome_fantasia || selectedCustomer.value.razao_social;
    }
    return 'Preencha os dados do cliente';
  });

  return {
    isOpen,
    mode,
    selectedCustomer,
    onCreatedCallback,
    onUpdatedCallback,
    isCreateMode,
    isEditMode,
    isViewMode,
    modalTitle,
    modalSubtitle,
    openCreateModal,
    openEditModal,
    openViewModal,
    openCreateModalWithCallback,
    openEditModalWithCallback,
    closeModal,
  };
}
