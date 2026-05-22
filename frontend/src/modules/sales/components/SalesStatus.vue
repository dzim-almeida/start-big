<script setup lang="ts">
import { computed} from 'vue';
import { Clock, CheckCircle2, XCircle, TrendingUp } from 'lucide-vue-next';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import { StatsCard } from '../types';

import { useSalesStatusQuery } from '../composables/queries/useSalesStatusQuery';

import { formatCurrency } from '@/shared/utils/finance';

const { data: stats } = useSalesStatusQuery();

const statsCards = computed((): StatsCard[] => [
  { key: 'vendas_em_orcamento', icon: Clock, label: 'Orçamentos', value: stats.value ? String(stats.value.vendas_em_orcamento) : '...' },
  { key: 'vendas_finalizadas', icon: CheckCircle2, label: 'Finalizadas', value: stats.value ? String(stats.value.vendas_finalizadas) : '...' },
  { key: 'vendas_canceladas', icon: XCircle, label: 'Canceladas', value: stats.value ? String(stats.value.vendas_canceladas) : '...' },
  { key: 'ticket_medio', icon: TrendingUp, label: 'Ticket Médio', currency: true, value: stats.value ? formatCurrency(stats.value.ticket_medio) : '...' },
]);
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 md:gap-6">
    <BaseStatsCard
      v-for="item in statsCards"
      :key="item.key"
      :icon="item.icon"
      :label="item.label"
      :value="item.value"
    />
  </div>
</template>
