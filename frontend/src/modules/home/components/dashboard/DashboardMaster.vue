<script setup lang="ts">
import { ref } from 'vue';
import { ArrowUpRight, ArrowDownRight } from 'lucide-vue-next';
import { storeToRefs } from 'pinia';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import OSVencendoTable from './OSVencendoTable.vue';
import EstoqueBaixoTable from './EstoqueBaixoTable.vue';
import RecentTransactions from './RecentTransactions.vue';
import RankingFuncionarios from './RankingFuncionarios.vue';
import OSPorStatusWidget from './OSPorStatusWidget.vue';
import FormasPagamentoWidget from './FormasPagamentoWidget.vue';
import OSAtrasadasEmpresaBanner from './OSAtrasadasEmpresaBanner.vue';

import { useAuthStore } from '@/shared/stores/auth.store';
import { useDashboard } from '../../composables/useDashboard';
import { useRankingFuncionariosQuery } from '../../composables/queries/useRankingFuncionariosQuery';
import { useOSPorStatusQuery } from '../../composables/queries/useOSPorStatusQuery';
import { useFormasPagamentoQuery } from '../../composables/queries/useFormasPagamentoQuery';
import { useOSAtrasadasEmpresaQuery } from '../../composables/queries/useOSAtrasadasEmpresaQuery';

import type { PeriodFilter } from '../../types/dashboard.types';

const authStore = useAuthStore();
const { userData, isLoading } = storeToRefs(authStore);

const activePeriodExtra = ref<PeriodFilter>('mes');

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

const rankingQuery   = useRankingFuncionariosQuery(activePeriodExtra);
const osPorStatusQuery = useOSPorStatusQuery();
const formasQuery    = useFormasPagamentoQuery(activePeriodExtra);
const atrasadasQuery = useOSAtrasadasEmpresaQuery();

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

    <!-- Banner OS Atrasadas (só aparece quando há) -->
    <OSAtrasadasEmpresaBanner
      :items="atrasadasQuery.data.value?.items ?? []"
      :total="atrasadasQuery.data.value?.total ?? 0"
    />

    <!-- Stats Section: Filter + Cards -->
    <div class="space-y-4">
      <div class="flex justify-end">
        <div class="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm text-xs font-semibold">
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

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <template v-if="isErrorStats">
          <div class="col-span-full bg-red-50 border border-red-200 rounded-2xl p-6 text-center text-red-600 text-sm font-medium">
            Erro ao carregar métricas. Tente recarregar a página.
          </div>
        </template>

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

    <!-- Período extra para widgets de análise -->
    <div class="flex items-center gap-3">
      <span class="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Análise por período</span>
      <div class="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm text-xs font-semibold">
        <button
          v-for="period in periods"
          :key="period.id"
          :class="[
            'px-3 py-1.5 rounded-lg transition-all duration-200',
            activePeriodExtra === period.id
              ? 'bg-zinc-900 text-white shadow-sm'
              : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50',
          ]"
          @click="activePeriodExtra = period.id"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <!-- Linha 1: Ranking (3/5) + OS por Status (2/5) -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div class="lg:col-span-3">
        <RankingFuncionarios
          :items="rankingQuery.data.value?.items ?? []"
          :is-loading="rankingQuery.isLoading.value"
          :is-error="rankingQuery.isError.value"
        />
      </div>
      <div class="lg:col-span-2">
        <OSPorStatusWidget
          :items="osPorStatusQuery.data.value?.items ?? []"
          :total-ativas="osPorStatusQuery.data.value?.total_ativas ?? 0"
          :is-loading="osPorStatusQuery.isLoading.value"
          :is-error="osPorStatusQuery.isError.value"
        />
      </div>
    </div>

    <!-- Linha 2: Formas de Pagamento (2/5) + OS Vencendo (3/5) -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div class="lg:col-span-2">
        <FormasPagamentoWidget
          :items="formasQuery.data.value?.items ?? []"
          :total="formasQuery.data.value?.total ?? 0"
          :is-loading="formasQuery.isLoading.value"
          :is-error="formasQuery.isError.value"
        />
      </div>
      <div class="lg:col-span-3">
        <OSVencendoTable :items="osVencendo" :is-loading="isLoadingOS" :is-error="isErrorOS" />
      </div>
    </div>

    <!-- Linha 3: Estoque Baixo (2/5) + Últimas Vendas (3/5) -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div class="lg:col-span-2">
        <EstoqueBaixoTable :items="estoqueBaixo" :is-loading="isLoadingEstoque" :is-error="isErrorEstoque" />
      </div>
      <div class="lg:col-span-3">
        <RecentTransactions :vendas="ultimasVendas" :is-loading="isLoadingVendas" :is-error="isErrorVendas" />
      </div>
    </div>

  </div>
</template>
