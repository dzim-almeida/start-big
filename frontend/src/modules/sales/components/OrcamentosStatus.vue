<script setup lang="ts">
import { computed } from 'vue';
import { FileText, ArrowRightLeft } from 'lucide-vue-next';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';

import { useOrcamentosStatusQuery } from '../composables/queries/useOrcamentosStatusQuery';

const { data: stats } = useOrcamentosStatusQuery();

const statsCards = computed(() => [
  { key: 'orcamentos_ativos', icon: FileText, label: 'Ativos', value: stats.value ? String(stats.value.orcamentos_ativos) : '...' },
  { key: 'orcamentos_convertidos', icon: ArrowRightLeft, label: 'Convertidos', value: stats.value ? String(stats.value.orcamentos_convertidos) : '...' },
]);
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 md:gap-6">
    <BaseStatsCard
      v-for="item in statsCards"
      :key="item.key"
      :icon="item.icon"
      :label="item.label"
      :value="item.value"
    />
  </div>
</template>
