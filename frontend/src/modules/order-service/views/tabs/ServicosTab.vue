<script setup lang="ts">
import { ref } from 'vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import ServicoStats from '../../components/servicos/ServicoStats.vue';
import ServicoTable from '../../components/servicos/ServicoTable.vue';
import ServicoFormModal from '../../components/servicos/ServicoFormModal.vue';
import { useService } from '../../composables/useService';
import { useServicoModal } from '../../composables/useServicoModal';
import type { ServiceReadZod } from '../../schemas/servicos.schema';

const { searchQuery, activeFilterQuery, currentPage, setPage, useServicesQuery, useServicosStatsQuery, useToggleServicoAtivoMutation } = useService();

const { services, totalPages, totalItems, isLoading, isError } = useServicesQuery();
const { stats, isLoading: isStatsLoading } = useServicosStatsQuery();
const { openEditModal, openViewModal } = useServicoModal();
const toggleAtivoMutation = useToggleServicoAtivoMutation();

const isStatusModalOpen = ref(false);
const servicoToToggle = ref<ServiceReadZod | null>(null);

function handleEdit(servico: ServiceReadZod) {
  openEditModal(servico);
}

function handleView(servico: ServiceReadZod) {
  openViewModal(servico);
}

function handleToggleStatus(servico: ServiceReadZod) {
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

    <ServicoStats :stats="stats" :loading="isStatsLoading" />

    <ServicoTable
      :servicos="services ?? []"
      :is-loading="isLoading"
      :is-error="isError"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      v-model:search="searchQuery"
      v-model:status-filter="activeFilterQuery"
      @view="handleView"
      @edit="handleEdit"
      @toggle-status="handleToggleStatus"
      @update:current-page="setPage"
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
