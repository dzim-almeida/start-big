<script setup lang="ts">
/**
 * @component CustomerFormModal
 * @description Modal for creating and editing customers (PF and PJ)
 * Uses provide/inject pattern through useCustomerFormProvider
 */

import { watch, onMounted, onUnmounted } from 'vue';
import { X } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTab from '@/shared/components/ui/BaseTab/BaseTab.vue';
import AddressSection from '@/shared/components/form/AddressSection.vue';

import { useCustomerModal } from '../composables/useCustomerModal';
import {
  useCustomerFormProvider,
  CUSTOMER_TYPE_TABS,
} from '../composables/useCustomerForm';

import PersonalDataSection from './form/PersonalDataSection.vue';
import CompanyDataSection from './form/CompanyDataSection.vue';
import ContactSection from './form/ContactSection.vue';
import NotesSection from './form/NotesSection.vue';

// =============================================
// Modal State
// =============================================

const {
  isOpen,
  isCreateMode,
  isEditMode,
  isViewMode,
  modalTitle,
  closeModal,
} = useCustomerModal();

// =============================================
// Form Management (provider)
// =============================================

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

// =============================================
// Keyboard & Scroll Management
// =============================================

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isOpen.value) {
    closeModal();
  }
}

function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    closeModal();
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

// Prevent body scroll when modal is open
watch(isOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : '';
});
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition
      enter-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        @click="handleBackdropClick"
      >
        <!-- Modal Content -->
        <Transition
          enter-active-class="transition-all duration-300"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-200"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="isOpen"
            class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col"
          >
            <!-- Header -->
            <div
              class="flex items-center justify-between px-6 py-4 border-b border-zinc-200"
            >
              <div>
                <h2 class="text-xl font-bold text-zinc-800">{{ modalTitle }}</h2>
              </div>
              <button
                type="button"
                class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                @click="closeModal"
              >
                <X :size="20" />
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 overflow-y-auto px-6 py-6">
              <!-- Customer Type Tabs -->
              <div v-if="isCreateMode" class="mb-6">
                <BaseTab
                  :tabs="CUSTOMER_TYPE_TABS"
                  :model-value="customerType"
                  :class="{ 'pointer-events-none opacity-60': isEditMode }"
                  @update:model-value="setCustomerType"
                />
              </div>

              <!-- API Error Alert -->
              <div
                v-if="apiError"
                class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
              >
                {{ apiError }}
              </div>

              <!-- Form -->
              <form class="space-y-8" @submit.prevent="onSubmit">
                <!-- PF Specific Section -->
                <PersonalDataSection
                  v-if="customerType === 'PF'"
                  :disabled="isViewMode"
                />

                <!-- PJ Specific Section -->
                <CompanyDataSection
                  v-if="customerType === 'PJ'"
                  :disabled="isViewMode"
                />

                <!-- Contact Section (common) -->
                <ContactSection :disabled="isViewMode" />

                <!-- Address Section (common) -->
                <AddressSection
                  v-model="enderecos"
                  :onAdd="handleAddAddress"
                  :onRemove="handleRemoveAddress"
                  :submit-count="submitCount"
                  :disabled="isViewMode"
                />

                <!-- Notes Section (common) -->
                <NotesSection :disabled="isViewMode" />
              </form>
            </div>

            <!-- Footer -->
            <div
              class="flex justify-end gap-3 px-6 py-4 border-t border-zinc-200"
            >
              <BaseButton
                type="button"
                variant="secondary"
                :disabled="isPending"
                @click="closeModal"
              >
                {{ isViewMode ? 'Fechar' : 'Cancelar' }}
              </BaseButton>
              <BaseButton
                v-if="!isViewMode"
                type="button"
                :is-loading="isPending"
                @click="onSubmit"
              >
                {{ isCreateMode ? 'Cadastrar' : 'Salvar Alterações' }}
              </BaseButton>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
