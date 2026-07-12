<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import OSFormHeader from './OSFormHeader.vue';
import OSFormFooter from './OSFormFooter.vue';
import OSFormSidebar from './OSFormSidebar.vue';
import OSControlsCard from './OSControlsCard.vue';
import OSFormTabsContent from './OSFormTabsContent.vue';
import { useOSFormView } from '../../context/useOSFormView.context';
import { useAuthStore } from '@/shared/stores/auth.store';
import { useSegmento } from '@/shared/composables/useSegmento';
import { computed, watch } from 'vue';

const view = useOSFormView();
const authStore = useAuthStore();
const { isOficinaMecanica } = useSegmento();

const canSelectTecnico = computed(() => {
  const user = authStore.userData;
  if (!user) return false;
  if (!user.cargo) return false;
  const p = user.cargo.permissoes;
  return p?.['all'] === true || p?.['funcionario'] === true;
});

watch(
  () => authStore.userData?.funcionario_id,
  (funcionarioId) => {
    if (!canSelectTecnico.value && funcionarioId) {
      view.handleFuncionarioIdUpdate(String(funcionarioId));
    }
  },
  { immediate: true },
);
</script>

<template>
  <BaseModal :is-open="view.isOpen.value" title="" size="4xl" @close="view.handleClose">
    <template #header>
      <OSFormHeader
        :os-number="view.currentOSData.value?.numero_os ?? '...'"
        :is-finalizada="view.isFinalizada.value"
        :is-cancelada="view.isCancelada.value"
        :is-create-mode="view.isCreateMode.value"
        @close="view.handleClose"
      />
    </template>

    <form class="space-y-4" @submit.prevent="view.handleLocalSubmit">
      
      <!-- Status Bar Operacional -->
      <OSControlsCard
        :status="view.controlsStatus.value"
        :is-create-mode="view.isCreateMode.value"
        :funcionario-id="view.controlsFuncionarioId.value"
        :prioridade="view.controlsPrioridade.value"
        :data-previsao="view.controlsDataPrevisao.value"
        :status-options="view.statusOptions.value"
        :prioridade-options="view.prioridadeOptions.value"
        :funcionarios-options="view.funcionariosOptions.value"
        :errors="view.formErrors.value"
        :can-select-tecnico="canSelectTecnico"
        :is-locked="view.isStructureLocked.value"
        @update:status="view.handleStatusUpdate"
        @update:funcionario-id="view.handleFuncionarioIdUpdate"
        @update:prioridade="view.handlePrioridadeUpdate"
        @update:data-previsao="view.handleDataPrevisaoUpdate"
      />

      <div class="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-5 items-start">
        <OSFormTabsContent />
        <OSFormSidebar />
      </div>
    </form>

    <template #footer>
      <OSFormFooter
        :is-finalizada="view.isFinalizada.value"
        :is-cancelada="view.isCancelada.value"
        :is-edit-mode="view.isEditMode.value"
        :is-create-mode="view.isCreateMode.value"
        :is-pending="view.isPending.value"
        :reopen-mode="view.reopenMode.value"
        :os-id="view.currentOSData.value?.id"
        :show-ficha="isOficinaMecanica"
        @finalizar="view.handleFinalizarOS"
        @print="view.printEntrada"
        @reprint-exit="view.printSaida"
        @reopen="view.handleReopenClick"
        @print-ficha="view.imprimirFicha"
        @save="view.handleLocalSubmit"
      />
    </template>
  </BaseModal>
</template>
