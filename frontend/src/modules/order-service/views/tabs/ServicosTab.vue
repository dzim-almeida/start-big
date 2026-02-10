<script setup lang="ts">
import { ref } from 'vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import ServicoStats from '../../components/servicos/ServicoStats.vue';
import ServicoTable from '../../components/servicos/ServicoTable.vue';
import ServicoFormModal from '../../components/servicos/ServicoFormModal.vue';
import { useServicos } from '../../composables/useServicos';
import { useToggleServicoAtivoMutation } from '../../composables/useServiceQuery';
import { useServicoModal } from '../../composables/useServicoModal';
import type { ServicoRead } from '../../types/servicos.types';

const { servicos, stats, searchQuery, statusFilter, isLoading, isError } = useServicos();
const { openEditModal, openViewModal } = useServicoModal();
const toggleAtivoMutation = useToggleServicoAtivoMutation();

const isStatusModalOpen = ref(false);
const servicoToToggle = ref<ServicoRead | null>(null);

function handleEdit(servico: ServicoRead) {
  openEditModal(servico);
}

function handleView(servico: ServicoRead) {
  openViewModal(servico);
}

function handleToggleStatus(servico: ServicoRead) {
  servicoToToggle.value = servico;
  isStatusModalOpen.value = true;
}

function handleCloseStatusModal() {
  isStatusModalOpen.value = false;
  servicoToToggle.value = null;
}

function handleConfirmStatusToggle() {
  if (!servicoToToggle.value) return;

  toggleAtivoMutation.mutate(servicoToToggle.value.id, {
    onSuccess: () => {
      handleCloseStatusModal();
    },
  });
}
</script>

<template>
  <div class="space-y-6">
    <ServicoStats :stats="stats" :loading="isLoading" />

    <ServicoTable
      :servicos="servicos"
      :is-loading="isLoading"
      :is-error="isError"
      v-model:search="searchQuery"
      v-model:status-filter="statusFilter"
      @view="handleView"
      @edit="handleEdit"
      @toggle-status="handleToggleStatus"
    />

    <ServicoFormModal />

    <BaseConfirmModal
      :is-open="isStatusModalOpen"
      :title="(servicoToToggle?.ativo ? 'Desativar' : 'Ativar') + ' Serviço?'"
      :description="`Deseja realmente ${servicoToToggle?.ativo ? 'desativar' : 'ativar'} o serviço <b>${servicoToToggle?.descricao}</b>?`"
      :confirm-text="servicoToToggle?.ativo ? 'DESATIVAR' : 'ATIVAR'"
      :is-danger="servicoToToggle?.ativo"
      :is-loading="toggleAtivoMutation.isPending.value"
      @close="handleCloseStatusModal"
      @confirm="handleConfirmStatusToggle"
    />
  </div>
</template>
