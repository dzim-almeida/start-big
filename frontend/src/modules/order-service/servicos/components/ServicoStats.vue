<script setup lang="ts">
import type { Component } from 'vue';
import { Wrench, CheckCircle2, Ban, CircleDollarSign } from 'lucide-vue-next';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  stats: {
    total: number;
    ativos: number;
    inativos: number;
    mediaValor: number;
  };
  loading?: boolean;
}

const props = defineProps<Props>();

interface CardInfo {
  key: 'total' | 'ativos' | 'inativos' | 'mediaValor';
  icon: Component;
  label: string;
}

const CARDS_INFO: CardInfo[] = [
  { key: 'total', icon: Wrench, label: 'Total de Serviços' },
  { key: 'ativos', icon: CheckCircle2, label: 'Serviços Ativos' },
  { key: 'inativos', icon: Ban, label: 'Serviços Inativos' },
  { key: 'mediaValor', icon: CircleDollarSign, label: 'Ticket Médio' },
];

function getCardValue(key: CardInfo['key']): string {
  if (props.loading) return '...';
  if (key === 'mediaValor') return formatCurrency(props.stats.mediaValor);
  return String(props.stats[key]);
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
    <BaseStatsCard
      v-for="item in CARDS_INFO"
      :key="item.key"
      :icon="item.icon"
      :label="item.label"
      :value="getCardValue(item.key)"
    />
  </div>
</template>
