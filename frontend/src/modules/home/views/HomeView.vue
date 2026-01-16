<script setup lang="ts">
import { ArrowUpRight, ArrowDownRight } from 'lucide-vue-next';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import RecentTransactions from '../components/dashboard/RecentTransactions.vue';
import { useDashboard } from '../composables/useDashboard';

import type { PeriodFilter } from '../types/dashboard.types';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';

import { useAuthStore } from '@/shared/stores/auth.store';

import { storeToRefs } from 'pinia';

const { activePeriod, stats, transactions, setPeriod } = useDashboard();

const authStore = useAuthStore();
const { userData, isLoading } = storeToRefs(authStore);

const periods: { id: PeriodFilter; label: string }[] = [
  { id: 'today', label: 'Hoje' },
  { id: 'week', label: 'Semana' },
  { id: 'month', label: 'Mês' },
];
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Welcome Header -->
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        :title="`Olá, ${userData?.nome}`"
        description="Confira os resultados da loja para hoje."
        :is-loading="isLoading"
      />

      <!-- Period Filter -->
      <div
        class="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm text-xs font-semibold self-start sm:self-auto"
      >
        <button
          v-for="period in periods"
          :key="period.id"
          :class="[
            'px-3 md:px-4 py-1.5 md:py-2 rounded-lg transition-all duration-200',
            activePeriod === period.id
              ? 'bg-zinc-900 text-white shadow-sm'
              : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50',
          ]"
          @click="setPeriod(period.id)"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
      <BaseStatsCard
        v-for="stat in stats"
        :key="stat.id"
        :icon="stat.icon"
        :label="stat.label"
        :value="stat.value"
      >
        <template #badge>
          <div
            :class="[
              'flex items-center gap-0.5 px-2 py-1 rounded-lg text-[10px] md:text-[11px] font-bold transition-transform group-hover:scale-105',
              stat.isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600',
            ]"
          >
            <ArrowUpRight v-if="stat.isPositive" :size="14" />
            <ArrowDownRight v-else :size="14" />
            <span>{{ stat.change }}</span>
          </div>
        </template>
      </BaseStatsCard>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
      <!-- Recent Transactions (2 columns) -->
      <div class="lg:col-span-3">
        <RecentTransactions :transactions="transactions" />
      </div>
    </div>
  </div>
</template>
