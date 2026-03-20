<script setup lang="ts">
/**
 * @component CustomerFormModal
 * @description Modal global para criar, editar e visualizar clientes (PF e PJ).
 * Renderizado uma única vez no MainLayout.vue.
 * Usa BaseModal + provide/inject para compartilhar estado com child components.
 */

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTab from '@/shared/components/ui/BaseTab/BaseTab.vue';
import AddressSection from '@/shared/components/form/AddressSection.vue';

import PersonalDataSection from './form/PersonalDataSection.vue';
import CompanyDataSection from './form/CompanyDataSection.vue';
import ContactSection from './form/ContactSection.vue';
import NotesSection from './form/NotesSection.vue';

import type { TipoCliente } from '@/modules/customers/types/clientes.types';
import { useCustomerModal } from '@/shared/composables/modals/customers/useCustomerModal';
import { useCustomerFormProvider } from '@/shared/composables/modals/customers/context/useCustomerForm.context';
import { CUSTOMER_TYPE_TABS } from '@/shared/composables/modals/customers/constants/customer.constant';

// ── Modal State ────────────────────────────────

const {
  isOpen,
  isCreateMode,
  isEditMode,
  isViewMode,
  modalTitle,
  modalSubtitle,
  closeModal,
} = useCustomerModal();

// ── Form Provider (DEVE ser chamado antes de qualquer await) ──

const {
  customerType,
  setCustomerType,
  enderecos,
  handleAddAddress,
  handleRemoveAddress,
  submitCount,
  apiError,
  isPending,
  onSubmit,
} = useCustomerFormProvider();
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="modalTitle"
    :subtitle="modalSubtitle"
    size="xl"
    @close="closeModal"
  >
    <!-- Customer Type Tabs (somente em criação) -->
    <div v-if="isCreateMode" class="mb-6">
      <BaseTab
        :tabs="CUSTOMER_TYPE_TABS"
        :model-value="customerType"
        :class="{ 'pointer-events-none opacity-60': isEditMode }"
        @update:model-value="(val: string) => setCustomerType(val as TipoCliente)"
      />
    </div>

    <!-- API Error Alert -->
    <div
      v-if="apiError"
      class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
    >
      {{ apiError }}
    </div>

    <!-- Formulário -->
    <form class="space-y-8" @submit.prevent="onSubmit">
      <PersonalDataSection
        v-if="customerType === 'PF'"
        :disabled="isViewMode"
      />

      <CompanyDataSection
        v-if="customerType === 'PJ'"
        :disabled="isViewMode"
      />

      <ContactSection :disabled="isViewMode" />

      <AddressSection
        v-model="enderecos"
        :onAdd="handleAddAddress"
        :onRemove="handleRemoveAddress"
        :submit-count="submitCount"
        :disabled="isViewMode"
      />

      <NotesSection :disabled="isViewMode" />
    </form>

    <!-- Footer -->
    <template #footer>
      <div class="flex justify-end gap-3">
        <BaseButton
          type="button"
          variant="secondary"
          :disabled="isPending"
          @click.stop="closeModal"
        >
          {{ isViewMode ? 'Fechar' : 'Cancelar' }}
        </BaseButton>
        <BaseButton
          v-if="!isViewMode"
          type="button"
          :is-loading="isPending"
          @click.stop="onSubmit"
        >
          {{ isCreateMode ? 'Cadastrar' : 'Salvar Alterações' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
