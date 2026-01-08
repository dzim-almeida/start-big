<script setup lang="ts">
import { StatCard, RecentTransactions, QuickActions } from '../components/dashboard';
import { useDashboard } from '../composables';
import type { PeriodFilter } from '../types/dashboard.types';

const { activePeriod, stats, transactions, quickActions, lowStockCount, setPeriod } =
  useDashboard();

const employee = {
  name: 'Gabriel',
};

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
      <div>
        <h2 class="text-xl md:text-2xl font-bold text-zinc-900">
          Olá, {{ employee.name }}
        </h2>
        <p class="text-zinc-500 text-xs md:text-sm mt-0.5">
          Confira os resultados da loja para hoje.
        </p>
      </div>

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
      <StatCard
        v-for="stat in stats"
        :key="stat.id"
        :icon="stat.icon"
        :label="stat.label"
        :value="stat.value"
        :change="stat.change"
        :is-positive="stat.isPositive"
      />
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
      <!-- Recent Transactions (2 columns) -->
      <div class="lg:col-span-2">
        <RecentTransactions :transactions="transactions" />
      </div>

      <!-- Quick Actions (1 column) -->
      <div class="lg:col-span-1">
        <QuickActions :actions="quickActions" :low-stock-count="lowStockCount" />
      </div>
    </div>
  </div>
</template>
