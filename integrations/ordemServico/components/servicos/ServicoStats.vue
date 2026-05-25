<!--
===========================================================================
ARQUIVO: ServicoStats.vue
MODULO: Ordem de Servico
DESCRICAO: Cards de estatisticas para o catalogo de servicos. Exibe
           contadores de total, ativos, inativos e ticket medio.
===========================================================================

PROPS:
- stats: Objeto com contadores { total, ativos, inativos, mediaValor }
- loading: Estado de carregamento (exibe skeleton)

LAYOUT:
- Grid responsivo: 1 coluna (mobile) / 2 colunas (tablet) / 4 colunas (desktop)
- Cards com icone, label e valor numerico

CARDS:
1. Total de Servicos - Icone Wrench (cinza)
2. Ativos - Icone CheckCircle2 (verde)
3. Inativos - Icone Ban (vermelho)
4. Ticket Medio - Icone CircleDollarSign (laranja) - valor formatado
===========================================================================
-->
<script setup lang="ts">
import { Wrench, CheckCircle2, Ban, CircleDollarSign } from 'lucide-vue-next';
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

defineProps<Props>();
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
    <!-- Total -->
    <div class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5 group">
      <div class="flex items-center justify-between mb-4">
          <div class="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl flex items-center justify-center border transition-colors bg-zinc-50 text-zinc-900 border-zinc-100">
             <Wrench :size="20" class="md:w-6 md:h-6" />
          </div>
      </div>
      <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">Total de Serviços</p>
      
      <div v-if="loading" class="h-8 md:h-9 w-24 bg-zinc-100 rounded-lg animate-pulse"></div>
      <p v-else class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">{{ stats.total }}</p>
    </div>

    <!-- Ativos -->
    <div class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5 group">
      <div class="flex items-center justify-between mb-4">
          <div class="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl flex items-center justify-center border transition-colors bg-emerald-50 text-emerald-600 border-emerald-100">
             <CheckCircle2 :size="20" class="md:w-6 md:h-6" />
          </div>
      </div>
      <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">Ativos</p>
      
      <div v-if="loading" class="h-8 md:h-9 w-24 bg-zinc-100 rounded-lg animate-pulse"></div>
      <p v-else class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">{{ stats.ativos }}</p>
    </div>

    <!-- Inativos -->
    <div class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5 group">
      <div class="flex items-center justify-between mb-4">
          <div class="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl flex items-center justify-center border transition-colors bg-red-50 text-red-600 border-red-100">
             <Ban :size="20" class="md:w-6 md:h-6" />
          </div>
      </div>
      <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">Inativos</p>
      
      <div v-if="loading" class="h-8 md:h-9 w-24 bg-zinc-100 rounded-lg animate-pulse"></div>
      <p v-else class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">{{ stats.inativos }}</p>
    </div>

    <!-- Ticket Medio -->
    <div class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5 group">
      <div class="flex items-center justify-between mb-4">
          <div class="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl flex items-center justify-center border transition-colors bg-orange-50 text-orange-600 border-orange-100">
             <CircleDollarSign :size="20" class="md:w-6 md:h-6" />
          </div>
      </div>
      <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">Ticket Médio</p>
      
      <div v-if="loading" class="h-8 md:h-9 w-24 bg-zinc-100 rounded-lg animate-pulse"></div>
      <p v-else class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">{{ formatCurrency(stats.mediaValor) }}</p>
    </div>
  </div>
</template>
