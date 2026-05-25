<!--
===========================================================================
ARQUIVO: OSStats.vue
MODULO: Ordem de Servico
DESCRICAO: Cards de estatisticas para o dashboard de OS. Exibe contadores
           de total, abertas, em andamento e finalizadas.
===========================================================================

PROPS:
- stats: Objeto com contadores { total, abertas, emAndamento, finalizadas }
- loading: Estado de carregamento (exibe skeleton)

LAYOUT:
- Grid responsivo: 1 coluna (mobile) / 2 colunas (tablet) / 4 colunas (desktop)
- Cards com icone, label e valor numerico
- Cores semanticas por tipo de status

CARDS:
1. Total de OS - Icone ClipboardList (cinza)
2. Abertas - Icone Clock (azul)
3. Em Andamento - Icone PlayCircle (amarelo)
4. Finalizadas - Icone CheckCircle2 (verde)
===========================================================================
-->
<script setup lang="ts">
import { ClipboardList, Clock, PlayCircle, CheckCircle2 } from 'lucide-vue-next';

interface Props {
  stats: {
    total: number;
    abertas: number;
    emAndamento: number;
    finalizadas: number;
  };
  loading?: boolean;
}

defineProps<Props>();

const statsConfig = [
  {
    key: 'total',
    label: 'Total de OS',
    icon: ClipboardList,
    colorClass: 'bg-zinc-50 text-zinc-900 border-zinc-100',
  },
  {
    key: 'abertas',
    label: 'Abertas',
    icon: Clock,
    colorClass: 'bg-brand-primary-light text-brand-primary border-brand-primary-light',
  },
  {
    key: 'emAndamento',
    label: 'Em Andamento',
    icon: PlayCircle,
    colorClass: 'bg-yellow-50 text-yellow-600 border-yellow-100',
  },
  {
    key: 'finalizadas',
    label: 'Finalizadas',
    icon: CheckCircle2,
    colorClass: 'bg-emerald-50 text-emerald-600 border-emerald-100',
  },
] as const;
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
    <div
      v-for="stat in statsConfig"
      :key="stat.key"
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
          <component :is="stat.icon" :size="20" class="md:w-6 md:h-6" />
        </div>
      </div>

      <!-- Label -->
      <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">
        {{ stat.label }}
      </p>

      <!-- Valor com Loading -->
      <div v-if="loading" class="h-8 md:h-9 w-24 bg-zinc-100 rounded-lg animate-pulse"></div>
      <p v-else class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">
        {{ stats[stat.key as keyof typeof stats] }}
      </p>
    </div>
  </div>
</template>
