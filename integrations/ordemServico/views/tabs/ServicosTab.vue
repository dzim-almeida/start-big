<!--
===========================================================================
ARQUIVO: ServicosTab.vue
MODULO: Ordem de Servico
DESCRICAO: Tab de gerenciamento do catalogo de servicos. Inclui listagem,
           criacao, edicao e ativacao/desativacao de servicos.
===========================================================================

COMPOSABLES:
- useServicos: Listagem, filtragem e paginacao de servicos
- useServicoActions: Mutations para toggle de status

COMPONENTES:
- ServicoStats: Cards de estatisticas
- ServicoTable: Tabela com busca e acoes
- ServicoFormModal: Modal de cadastro/edicao
- BaseConfirmModal: Modal de confirmacao para toggle

FUNCIONALIDADES:
- Listagem paginada de servicos (10 por pagina)
- Busca por descricao
- Filtro por status (todos/ativos/inativos)
- Cadastro de novo servico
- Edicao de servico existente
- Ativacao/desativacao com confirmacao

EXPOSE:
- handleOpenModal: Permite que OrdemServicoView abra o modal externamente
===========================================================================
-->
<script setup lang="ts">
import { ref } from 'vue';
import ServicoTable from '../../components/servicos/ServicoTable.vue';
import ServicoFormModal from '../../components/servicos/ServicoFormModal.vue';
import ServicoStats from '../../components/servicos/ServicoStats.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import { useServicos, useServicoActions } from '../../composables';
import type { ServicoRead } from '../../types/servicos.types';

const {
  servicos,
  stats,
  searchQuery,
  statusFilter,
  isLoading,
  error,
  setSearch,
  setFilter,
  // Paginacao
  currentPage,
  totalPages,
  setPage
} = useServicos();

const { 
    toggleAtivoMutation,
    isPending: isActionsPending
} = useServicoActions();

const isModalOpen = ref(false);
const selectedServico = ref<ServicoRead | null>(null);

// Modal de Status
const isStatusModalOpen = ref(false);
const servicoToToggle = ref<ServicoRead | null>(null);

function handleSearch(value: string) {
  setSearch(value);
}

function handleFilterChange(value: string) {
  setFilter(value as any);
}

function handleOpenModal() {
  selectedServico.value = null;
  isModalOpen.value = true;
}

function handleCloseModal() {
  isModalOpen.value = false;
  selectedServico.value = null;
}

function handleEdit(servico: ServicoRead) {
  selectedServico.value = servico;
  isModalOpen.value = true;
}

// Logic para Confirm Modal
function handleToggleStatus(servico: ServicoRead) {
  servicoToToggle.value = servico;
  isStatusModalOpen.value = true;
}

function handleCloseStatusModal() {
  isStatusModalOpen.value = false;
  servicoToToggle.value = null;
}

function handleConfirmStatusToggle() {
  if (servicoToToggle.value) {
    toggleAtivoMutation.mutate(servicoToToggle.value.id, {
        onSuccess: () => handleCloseStatusModal()
    });
  }
}

defineExpose({
  handleOpenModal,
});
</script>

<template>
  <div class="space-y-6">
    <!-- Stats Cards -->
    <ServicoStats :stats="stats" :loading="isLoading" />

    <!-- Error State -->
    <div
      v-if="error"
      class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
    >
      Erro ao carregar serviços. Verifique sua conexão e tente novamente.
    </div>

    <!-- Table -->
    <ServicoTable
      :servicos="servicos"
      :is-loading="isLoading"
      :search-query="searchQuery"
      :active-filter-status="statusFilter"
      :current-page="currentPage"
      :total-pages="totalPages"
      @edit="handleEdit"
      @toggle-status="handleToggleStatus"
      @search="handleSearch"
      @filter-change="handleFilterChange"
      @page-change="setPage"
    />

    <!-- Modal Formulario -->
    <ServicoFormModal 
        :is-open="isModalOpen" 
        :servico="selectedServico" 
        @close="handleCloseModal" 
    />

    <!-- Modal de Desativacao/Ativacao (Shared) -->
    <BaseConfirmModal
      :is-open="isStatusModalOpen"
      :title="(servicoToToggle?.ativo ? 'Desativar' : 'Ativar') + ' Serviço?'"
      :description="`Deseja realmente ${servicoToToggle?.ativo ? 'desativar' : 'ativar'} o serviço <b>${servicoToToggle?.descricao}</b>?`"
      :confirm-text="servicoToToggle?.ativo ? 'DESATIVAR' : 'ATIVAR'"
      :is-danger="servicoToToggle?.ativo"
      :is-loading="isActionsPending"
      @close="handleCloseStatusModal"
      @confirm="handleConfirmStatusToggle"
    />
  </div>
</template>
