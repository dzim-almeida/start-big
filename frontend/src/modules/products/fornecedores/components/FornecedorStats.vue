<script setup lang="ts">
import { Truck, CheckCircle2, XCircle } from 'lucide-vue-next';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';

interface Props {
  total: number;
  ativos: number;
  inativos: number;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), { loading: false });

const CARDS = [
  { key: 'total' as const, icon: Truck, label: 'Total de Fornecedores' },
  { key: 'ativos' as const, icon: CheckCircle2, label: 'Fornecedores Ativos' },
  { key: 'inativos' as const, icon: XCircle, label: 'Fornecedores Inativos' },
];
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 md:gap-6">
    <BaseStatsCard
      v-for="card in CARDS"
      :key="card.key"
      :icon="card.icon"
      :label="card.label"
      :value="props.loading ? '—' : String(props[card.key])"
    />
  </div>
</template>
