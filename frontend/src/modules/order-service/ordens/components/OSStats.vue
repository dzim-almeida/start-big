<script setup lang="ts">
import type { Component } from 'vue';
import { ClipboardList, Clock, PlayCircle, CheckCircle2 } from 'lucide-vue-next';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';

interface Props {
  stats: {
    total: number;
    abertas: number;
    emAndamento: number;
    finalizadas: number;
  };
  loading?: boolean;
}

const props = defineProps<Props>();

interface CardInfo {
  key: 'total' | 'abertas' | 'emAndamento' | 'finalizadas';
  icon: Component;
  label: string;
}

const CARDS_INFO: CardInfo[] = [
  { key: 'total',       icon: ClipboardList, label: 'Total de OS'  },
  { key: 'abertas',     icon: Clock,         label: 'Abertas'      },
  { key: 'emAndamento', icon: PlayCircle,    label: 'Em Andamento' },
  { key: 'finalizadas', icon: CheckCircle2,  label: 'Finalizadas'  },
];

function getCardValue(key: CardInfo['key']): string {
  if (props.loading) return '...';
  return String(props.stats[key]);
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 md:gap-6">
    <BaseStatsCard
      v-for="item in CARDS_INFO"
      :key="item.key"
      :icon="item.icon"
      :label="item.label"
      :value="getCardValue(item.key)"
    />
  </div>
</template>
