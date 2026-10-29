<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useServicoModal } from '../composables/useServicoModal';
import { useServicoFormProvider } from '../composables/useServicoForm';
import ServicoDadosSection from './form/ServicoDadosSection.vue';
import DadosFiscaisSection from './form/DadosFiscaisSection.vue';

const { isOpen, isCreateMode, isViewMode, modalTitle, closeModal, switchToEdit } = useServicoModal();
const { onSubmit, isPending, submitCount, apiError, nfseDisponivel } = useServicoFormProvider();
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
        <!-- A seção fiscal existia desde o Centro Fiscal (97e64d39) mas nunca
             foi montada. Entra com a NFS-e (docs/nfse-plano.md, F1), só para
             quem tem o módulo: para as outras lojas o modal não muda. -->
        <DadosFiscaisSection
          v-if="nfseDisponivel"
          :submit-count="submitCount"
          :disabled="isViewMode"
          :is-create-mode="isCreateMode"
        />
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
          v-if="isViewMode"
          type="button"
          variant="primary"
          @click="switchToEdit"
        >
          Editar
        </BaseButton>
        <BaseButton
          v-else
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
