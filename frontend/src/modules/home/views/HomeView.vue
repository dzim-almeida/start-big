<script setup lang="ts">
import { ArrowUpRight, ArrowDownRight } from 'lucide-vue-next';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import OSVencendoTable from '../components/dashboard/OSVencendoTable.vue';
import EstoqueBaixoTable from '../components/dashboard/EstoqueBaixoTable.vue';
import RecentTransactions from '../components/dashboard/RecentTransactions.vue';
import { useDashboard } from '../composables/useDashboard';

import type { PeriodFilter } from '../types/dashboard.types';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';

import { useAuthStore } from '@/shared/stores/auth.store';

import { storeToRefs } from 'pinia';

const {
  activePeriod,
  stats,
  setPeriod,
  periodDescription,
  osVencendo,
  estoqueBaixo,
  ultimasVendas,
  isLoadingStats,
  isLoadingOS,
  isLoadingEstoque,
  isLoadingVendas,
  isErrorStats,
  isErrorOS,
  isErrorEstoque,
  isErrorVendas,
} = useDashboard();

const authStore = useAuthStore();
const { userData, isLoading } = storeToRefs(authStore);

const periods: { id: PeriodFilter; label: string }[] = [
  { id: 'hoje', label: 'Hoje' },
  { id: 'semana', label: 'Semana' },
  { id: 'mes', label: 'Mês' },
];
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Welcome Header -->
    <PageReview
      :title="`Olá, ${userData?.nome}`"
      :description="periodDescription"
      :is-loading="isLoading"
    />

    <!-- Stats Section: Filter + Cards -->
    <div class="space-y-4">
      <!-- Period Filter -->
      <div class="flex justify-end">
        <div
          class="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm text-xs font-semibold"
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
        <!-- Error state -->
        <template v-if="isErrorStats">
          <div
            class="col-span-full bg-red-50 border border-red-200 rounded-2xl p-6 text-center text-red-600 text-sm font-medium"
          >
            Erro ao carregar métricas. Tente recarregar a página.
          </div>
        </template>

        <!-- Loading skeletons -->
        <template v-else-if="isLoadingStats">
        <div
          v-for="i in 4"
          :key="i"
          class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="w-10 h-10 md:w-12 md:h-12 bg-zinc-100 rounded-xl md:rounded-2xl animate-pulse" />
            <div class="w-16 h-6 bg-zinc-100 rounded-lg animate-pulse" />
          </div>
          <div class="w-20 h-3 bg-zinc-100 rounded animate-pulse mb-2" />
          <div class="w-28 h-7 bg-zinc-100 rounded animate-pulse" />
        </div>
      </template>

      <!-- Real stats -->
      <template v-else>
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
      </template>
      </div>
    </div>

    <!-- Info Tables: 2-column layout (40% / 60%) -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <!-- Esquerda: Estoque + Vendas (2/5 = 40%) -->
      <div class="lg:col-span-2 space-y-6">
        <EstoqueBaixoTable :items="estoqueBaixo" :is-loading="isLoadingEstoque" :is-error="isErrorEstoque" />
        <RecentTransactions :vendas="ultimasVendas" :is-loading="isLoadingVendas" :is-error="isErrorVendas" />
      </div>

      <!-- Direita: OS Vencendo (3/5 = 60%) -->
      <div class="lg:col-span-3">
        <OSVencendoTable :items="osVencendo" :is-loading="isLoadingOS" :is-error="isErrorOS" />
      </div>
    </div>
  </div>
</template>
