<script setup lang="ts">
import type { Component } from 'vue';
import { ClipboardList, Clock, CheckCircle2, TrendingUp } from 'lucide-vue-next';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import { formatCurrency } from '@/shared/utils/finance';

interface Props {
  stats: {
    total: number;
    abertas: number;
    finalizadas: number;
    ticket_medio: number;
  };
  loading?: boolean;
}

const props = defineProps<Props>();

interface CardInfo {
  key: 'total' | 'abertas' | 'finalizadas' | 'ticket_medio';
  icon: Component;
  label: string;
  currency?: boolean;
}

const CARDS_INFO: CardInfo[] = [
  { key: 'total',        icon: ClipboardList, label: 'Total de OS'  },
  { key: 'abertas',      icon: Clock,         label: 'Abertas'      },
  { key: 'finalizadas',  icon: CheckCircle2,  label: 'Finalizadas'  },
  { key: 'ticket_medio', icon: TrendingUp,    label: 'Ticket Médio', currency: true },
];

function getCardValue(card: CardInfo): string {
  if (props.loading) return '...';
  if (card.currency) return formatCurrency(props.stats[card.key]);
  return String(props.stats[card.key]);
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 md:gap-6">
    <BaseStatsCard
      v-for="item in CARDS_INFO"
      :key="item.key"
      :icon="item.icon"
      :label="item.label"
      :value="getCardValue(item)"
    />
  </div>
</template>
