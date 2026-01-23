<script setup lang="ts">
/**
 * @component EmployeesView
 * @description Main employees list view with real API data
 */

import { ref, computed, watch } from 'vue';
import { Plus } from 'lucide-vue-next';

import { TAB_OPTIONS, CARDS_INFO } from '../constants/employees.constants';

import EmployeeTable from '../components/EmployeeTable.vue';
import EmployeeModal from '../components/EmployeeModal.vue';
import PositionsPanel from '../components/PositionsPanel.vue';
import PositionModal from '../components/PositionModal.vue';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTab2 from '@/shared/components/ui/BaseTab2/BaseTab2.vue';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useEmployeesQuery } from '../composables/useEmployeesQuery';
import { useEmployeeModal } from '../composables/useEmployeeModal';
import { usePositionsQuery, useDeletePositionMutation } from '../composables/usePositionsQuery';
import { usePositionModal } from '../composables/usePositionModal';

// =============================================
// State
// =============================================

const activeTeam = ref('employee');
const searchTerm = ref('');
const positionSearchTerm = ref('');

watch(activeTeam, (value) => {
  if (value === 'employee') {
    positionSearchTerm.value = '';
  }
});

// =============================================
// Data Fetching
// =============================================

const { data: employees, isLoading, isError } = useEmployeesQuery(searchTerm);
const {
  data: positions,
  isLoading: isPositionsLoading,
  isError: isPositionsError,
} = usePositionsQuery(positionSearchTerm);

// =============================================
// Modal Controls
// =============================================

const { openCreateModal } = useEmployeeModal();
const {
  openCreateModal: openCreatePositionModal,
  openEditModal: openEditPositionModal,
  openViewModal: openViewPositionModal,
} = usePositionModal();

const deletePositionMutation = useDeletePositionMutation();

// =============================================
// Computed Stats
// =============================================

const stats = computed(() => ({
  all_employees: employees.value?.length || 0,
  actives_now: employees.value?.filter((e) => e.ativo).length || 0,
  in_vacation: 0, // Backend doesn't track this yet
  left_employees: employees.value?.filter((e) => !e.ativo).length || 0,
}));

const pageTitle = computed(() =>
  activeTeam.value === 'employee' ? 'Funcionarios' : 'Cargos',
);

const pageDescription = computed(() =>
  activeTeam.value === 'employee'
    ? 'Veja como estão seus funcionarios hoje.'
    : 'Configure funções e permissões da sua organizacao.',
);

// =============================================
// Handlers
// =============================================

function handleAddClick() {
  if (activeTeam.value === 'employee') {
    openCreateModal();
  } else {
    openCreatePositionModal();
  }
}

function handleViewPosition(positionId: number) {
  const position = positions.value?.find((item) => item.id === positionId);
  if (position) openViewPositionModal(position);
}

function handleEditPosition(positionId: number) {
  const position = positions.value?.find((item) => item.id === positionId);
  if (position) openEditPositionModal(position);
}

function handleRemovePosition(positionId: number) {
  const position = positions.value?.find((item) => item.id === positionId);
  if (!position) return;
  deletePositionMutation.mutate(positionId);
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Header -->
    <div
      class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4"
    >
      <PageReview
        :title="pageTitle"
        :description="pageDescription"
      />

      <div class="flex gap-5">
        <BaseTab2 :options="TAB_OPTIONS" v-model="activeTeam" />
        <BaseButton
          variant="primary"
          size="md"
          type="button"
          class="flex gap-1"
          @click="handleAddClick"
        >
          <Plus :size="20" />
          {{
            activeTeam === 'employee'
              ? 'Adicionar Funcionario'
              : 'Adicionar Cargo'
          }}
        </BaseButton>
      </div>
    </div>

    <template v-if="activeTeam === 'employee'">
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 md:gap-6">
        <BaseStatsCard
          v-for="item in CARDS_INFO"
          :key="item.key"
          :icon="item.icon"
          :label="item.label"
          :value="String(stats[item.key])"
        />
      </div>

      <!-- Employee Table -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
        <div class="lg:col-span-3">
          <EmployeeTable
            :employees="employees || []"
            :positions="positions || []"
            :is-loading="isLoading"
            :is-error="isError"
            v-model:search="searchTerm"
          />
        </div>
      </div>
    </template>

    <template v-else>
      <PositionsPanel
        v-model:search="positionSearchTerm"
        :positions="positions || []"
        :employees="employees || []"
        :is-loading="isPositionsLoading"
        :is-error="isPositionsError"
        @view="(position) => handleViewPosition(position.id)"
        @edit="(position) => handleEditPosition(position.id)"
        @remove="(position) => handleRemovePosition(position.id)"
      />
    </template>

    <!-- Modal -->
    <EmployeeModal />
    <PositionModal />
  </div>
</template>
