<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useServicoModal } from '../composables/useServicoModal';
import { useServicoFormProvider } from '../composables/useServicoForm';
import ServicoDadosSection from './form/ServicoDadosSection.vue';

const { isOpen, isCreateMode, isViewMode, modalTitle, closeModal } = useServicoModal();
const { onSubmit, isPending, submitCount, apiError } = useServicoFormProvider();
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="modalTitle"
    size="lg"
    @close="closeModal"
  >
    <div>
      <div
        v-if="apiError"
        class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm"
      >
        {{ apiError }}
      </div>

      <form id="servico-form" @submit.prevent="onSubmit" class="space-y-8">
        <ServicoDadosSection :submit-count="submitCount" :disabled="isViewMode" />
      </form>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton
          type="button"
          variant="secondary"
          @click="closeModal"
        >
          {{ isViewMode ? 'Fechar' : 'Cancelar' }}
        </BaseButton>
        <BaseButton
          v-if="!isViewMode"
          type="submit"
          variant="primary"
          :is-loading="isPending"
          @click="onSubmit"
        >
          {{ isCreateMode ? 'Cadastrar Serviço' : 'Salvar Alterações' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
