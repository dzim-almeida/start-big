<script setup lang="ts">
/**
 * @component EmployeesView
 * @description Main employees list view with real API data
 */

import { ref, computed } from 'vue';
import { Plus } from 'lucide-vue-next';

import { TAB_OPTIONS, CARDS_INFO } from '../constants/employees.constants';

import EmployeeTable from '../components/EmployeeTable.vue';
import EmployeeModal from '../components/EmployeeModal.vue';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useEmployeesQuery } from '../composables/useEmployeesQuery';
import { useEmployeeModal } from '../composables/useEmployeeModal';

// =============================================
// State
// =============================================

const activeTeam = ref('employee');
const searchTerm = ref('');

// =============================================
// Data Fetching
// =============================================

const { data: employees, isLoading, isError } = useEmployeesQuery(searchTerm);

// =============================================
// Modal Controls
// =============================================

const { openCreateModal } = useEmployeeModal();

// =============================================
// Computed Stats
// =============================================

const stats = computed(() => ({
  all_employees: employees.value?.length || 0,
  actives_now: employees.value?.filter((e) => e.ativo).length || 0,
  in_vacation: 0, // Backend doesn't track this yet
  left_employees: employees.value?.filter((e) => !e.ativo).length || 0,
}));

// =============================================
// Handlers
// =============================================

function handleAddClick() {
  if (activeTeam.value === 'employee') {
    openCreateModal();
  } else {
    // TODO: Open cargo modal
    console.log('Abrir modal de cargo');
  }
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Header -->
    <div
      class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4"
    >
      <PageReview
        title="Funcionarios"
        description="Veja como estao seus funcionarios hoje."
      />

      <div class="flex gap-5">
        <BaseFilter :options="TAB_OPTIONS" v-model="activeTeam" />
        <BaseButton
          variant="primary"
          size="sm"
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
          :is-loading="isLoading"
          :is-error="isError"
          v-model:search="searchTerm"
        />
      </div>
    </div>

    <!-- Modal -->
    <EmployeeModal />
  </div>
</template>
