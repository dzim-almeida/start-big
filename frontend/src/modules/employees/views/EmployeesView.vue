<script setup lang="ts">

import {
    Plus
} from 'lucide-vue-next'

import { TAB_OPTIONS, CARDS_INFO } from '../constants/employees.constats';

import EmployeeTable from '../components/EmployeeTable.vue';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { mockEmployees } from '../mock/employess.mock';

import { ref } from 'vue';

const activeTeam = ref('employee');

const isLoading = false;
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Welcome Header -->
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        title="Funcionários"
        description="Veja como estão seus funcionários hoje."
        :is-loading="isLoading"
      />

      <div class="flex gap-5">
        <BaseFilter :options="TAB_OPTIONS" v-model="activeTeam" />
        <BaseButton
          variant="primary"
          size="sm"
          type="button"
          class="flex gap-1"
        >
          <Plus :size="20" />
          {{ activeTeam === 'employee' ? 'Adicionar Funcionário' : 'Adicionar Cargo'}}
        </BaseButton>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 md:gap-6">
      <BaseStatsCard
        v-for="item in CARDS_INFO" :key="item.key"
        :icon="item.icon"
        :label="item.label"
        :value="2500"
      >
      </BaseStatsCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
      <!-- Recent Transactions (2 columns) -->
      <div class="lg:col-span-3">
        <EmployeeTable :employees="mockEmployees" />
      </div>
    </div>
  </div>
</template>
