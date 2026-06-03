<script setup lang="ts">
import { computed, watch } from 'vue';
import OSClientCard from './OSClientCard.vue';
import OSControlsCard from './OSControlsCard.vue';
import OSSummaryCard from './OSSummaryCard.vue';
import { useOSFormView } from '../../context/useOSFormView.context';
import { useAuthStore } from '@/shared/stores/auth.store';

const view = useOSFormView();
const authStore = useAuthStore();

const canSelectTecnico = computed(() => {
  const user = authStore.userData;
  if (!user) return false;
  if (!user.cargo) return true; // master sem cargo tem acesso total
  return user.cargo.permissoes?.['funcionario'] === true;
});

// Pré-preenche o técnico com o funcionário logado quando as opções carregam
watch(
  () => view.funcionariosOptions.value.length,
  (len) => {
    if (len > 1 && !canSelectTecnico.value && view.isCreateMode.value) {
      const funcionarioId = authStore.userData?.funcionario_id;
      if (funcionarioId) {
        view.handleFuncionarioIdUpdate(String(funcionarioId));
      }
    }
  },
  { immediate: true },
);
</script>

<template>
  <fieldset :disabled="view.isStructureLocked.value" class="contents lg:block space-y-4">
    <OSClientCard
      :cliente="view.currentCliente.value"
      :status="view.currentOSData.value?.status"
      :data-criacao="view.currentOSData.value?.data_criacao"
      :data-finalizacao="view.currentOSData.value?.data_finalizacao"
      :is-edit-mode="view.isEditMode.value"
      :is-finalizada="view.isFinalizada.value"
      @change-cliente="view.handleChangeCliente"
      @update-cliente="view.handleUpdateCliente"
      @open-historico="view.openHistoricoModal"
    />

    <OSControlsCard
      :status="view.controlsStatus.value"
      :is-create-mode="view.isCreateMode.value"
      :funcionario-id="view.controlsFuncionarioId.value"
      :prioridade="view.controlsPrioridade.value"
      :data-previsao="view.controlsDataPrevisao.value"
      :status-options="view.statusOptions.value"
      :prioridade-options="view.prioridadeOptions.value"
      :funcionarios-options="view.funcionariosOptions.value"
      :can-select-tecnico="canSelectTecnico"
      :errors="view.formErrors.value"
      @update:status="view.handleStatusUpdate"
      @update:funcionario-id="view.handleFuncionarioIdUpdate"
      @update:prioridade="view.handlePrioridadeUpdate"
      @update:data-previsao="view.handleDataPrevisaoUpdate"
    />

    <OSSummaryCard
      :itens="view.displayItems.value"
      :subtotal="view.displaySubtotal.value"
      :valor-entrega="view.displayValorEntrega.value"
      :valor-desconto="view.displayValorDesconto.value"
      :valor-total="view.displayValorTotal.value"
      :valor-entrada="view.displayValorEntrada.value"
      :is-locked="view.isStructureLocked.value"
      @update:valor-entrada="view.handleValorEntradaUpdate"
    />
  </fieldset>
</template>
