<script setup lang="ts">
/**
 * ===========================================================================
 * ARQUIVO: ClientStats.vue
 * MODULO: Clientes
 * DESCRICAO: Cards de estatisticas do modulo de clientes.
 *            Exibe total, ativos, PF e PJ.
 * ===========================================================================
 */

import { computed } from 'vue';
import type { ClienteStatsData } from '../../types/clientes.types';
import { STATS_CONFIG } from '../../constants/clientes.constants';

// ===========================================================================
// PROPS
// ===========================================================================

interface Props {
  stats: ClienteStatsData;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

// ===========================================================================
// COMPUTED - CARDS DE ESTATISTICAS
// ===========================================================================

const statCards = computed(() => {
  return STATS_CONFIG.map(config => ({
    ...config,
    value: config.getValue(props.stats)
  }));
});
</script>

<template>
  <!-- Grid responsivo dos cards de estatisticas -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
    <!-- Card individual -->
    <div
      v-for="stat in statCards"
      :key="stat.id"
      class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5 group"
    >
      <!-- Cabecalho: Icone -->
      <div class="flex items-center justify-between mb-4">
        <div
          :class="[
            'w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl flex items-center justify-center border transition-colors',
            stat.colorClass,
          ]"
        >
          <!-- Icone dinamico -->
          <component :is="stat.icon" :size="20" class="md:w-6 md:h-6" />
        </div>
      </div>

      <!-- Label do card -->
      <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">
        {{ stat.label }}
      </p>

      <!-- Valor numerico com Skeleton Loading -->
      <div v-if="loading" class="h-8 md:h-9 w-24 bg-zinc-100 rounded-lg animate-pulse"></div>
      <p v-else class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">
        {{ stat.value }}
      </p>
    </div>
  </div>
</template>
