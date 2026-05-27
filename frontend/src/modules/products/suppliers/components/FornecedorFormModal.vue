// ============================================================================
// COMPONENTE: Modal de Cadastro de Fornecedor (Sistema ERP Produto Motorista)
// RESPONSABILIDADE: Gerenciar o fluxo de entrada de dados de parceiros.
// ESTADO: Em desenvolvimento / Refatorado para Composables.
// ============================================================================
<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useFornecedorModal } from '../composables/useFornecedorModal';
import { useFornecedorFormProvider } from '../composables/useFornecedorForm';
import SupplierTypeSelector from './SupplierTypeSelector.vue';
import DadosFornecedorSection from './form/DadosFornecedorSection.vue';
import DadosTransportadoraSection from './form/DadosTransportadoraSection.vue';
import DadosEntregadorSection from './form/DadosEntregadorSection.vue';
import EnderecoFornecedorSection from './form/EnderecoFornecedorSection.vue';
import DadosBancariosSection from './form/DadosBancariosSection.vue';
import ObservacoesFornecedorSection from './form/ObservacoesFornecedorSection.vue';
import type { SupplierTipo } from '../types/fornecedor.types';

const {
  isOpen,
  isCreateMode,
  isViewMode,
  isTipoSelectionStep,
  selectedTipo,
  modalTitle,
  selectTipo,
  backToTipoSelection,
  closeModal,
} = useFornecedorModal();

const { onSubmit, isPending, submitCount, apiError } = useFornecedorFormProvider();

function handleSelectTipo(tipo: SupplierTipo) {
  selectTipo(tipo);
}
</script>

<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" size="2xl" @close="closeModal">
    <div>
      <div
        v-if="apiError"
        class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm"
      >
        {{ apiError }}
      </div>

      <!-- Etapa 1: Seleção do tipo -->
      <SupplierTypeSelector v-if="isTipoSelectionStep" @select="handleSelectTipo" />

      <!-- Etapa 2: Formulário conforme o tipo -->
      <form v-else id="fornecedor-form" @submit.prevent="onSubmit" class="space-y-8">
        <DadosFornecedorSection
          v-if="selectedTipo === 'produto'"
          :submit-count="submitCount"
          :disabled="isViewMode"
        />
        <DadosTransportadoraSection
          v-else-if="selectedTipo === 'transportadora'"
          :submit-count="submitCount"
          :disabled="isViewMode"
        />
        <DadosEntregadorSection
          v-else-if="selectedTipo === 'entregador'"
          :submit-count="submitCount"
          :disabled="isViewMode"
        />

        <hr class="border-zinc-100" />

        <EnderecoFornecedorSection
          :submit-count="submitCount"
          :disabled="isViewMode"
        />

        <hr class="border-zinc-100" />

        <DadosBancariosSection
          :submit-count="submitCount"
          :disabled="isViewMode"
        />

        <hr class="border-zinc-100" />

        <ObservacoesFornecedorSection :disabled="isViewMode" />
      </form>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <!-- Botão voltar (só no modo criação após selecionar tipo) -->
        <BaseButton
          v-if="isCreateMode && !isTipoSelectionStep"
          type="button"
          variant="secondary"
          @click="backToTipoSelection"
        >
          Voltar
        </BaseButton>
        <div v-else />

        <div class="flex items-center gap-3">
          <BaseButton type="button" variant="secondary" @click="closeModal">
            {{ isViewMode ? 'Fechar' : 'Cancelar' }}
          </BaseButton>
          <BaseButton
            v-if="!isViewMode && !isTipoSelectionStep"
            type="submit"
            variant="primary"
            :is-loading="isPending"
            @click="onSubmit"
          >
            {{ isCreateMode ? 'Cadastrar Fornecedor' : 'Salvar Alterações' }}
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>
</template>
