<script setup lang="ts">
/**
 * @fileoverview Margem orçada × real da OS da fábrica (F4).
 *
 * Orçado: a fração de chapa (com a perda) ao custo congelado na aprovação —
 * o que o preço cobriu. Real: as chapas INTEIRAS que saíram na separação, ao
 * custo do dia, mais o que a central de corte cobrou de fato. A margem real
 * só aparece com tudo separado e recebido; antes disso, é parcial.
 */
import { computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { TrendingDown, TrendingUp } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';

import { fabricaKeys } from '../constants/queryKeys';
import { getMargem } from '../services/fabrica.service';

const props = defineProps<{ numeroOs: string }>();

const { data } = useQuery({
  queryKey: computed(() => fabricaKeys.margem(props.numeroOs)),
  queryFn: () => getMargem(props.numeroOs),
});

function pct(bp: number | null): string {
  return bp == null ? '—' : `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

const piorou = computed(() =>
  data.value?.margem_real_bp != null && data.value.margem_orcada_bp != null
    ? data.value.margem_real_bp < data.value.margem_orcada_bp
    : false,
);
</script>

<template>
  <div v-if="data" class="rounded-xl border border-zinc-200 p-4 space-y-3">
    <p class="text-xs font-bold uppercase tracking-wider text-zinc-500">Margem orçada × real (versão {{ data.versao }})</p>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
      <div><p class="text-[11px] uppercase text-zinc-400 font-bold">Preço</p><p class="font-bold tabular-nums">{{ formatCurrency(data.preco) }}</p></div>
      <div><p class="text-[11px] uppercase text-zinc-400 font-bold">Custo orçado</p><p class="font-bold tabular-nums">{{ formatCurrency(data.custo_orcado) }}</p></div>
      <div>
        <p class="text-[11px] uppercase text-zinc-400 font-bold">Custo real{{ data.completo ? '' : ' (parcial)' }}</p>
        <p class="font-bold tabular-nums">{{ formatCurrency(data.custo_real) }}</p>
      </div>
      <div>
        <p class="text-[11px] uppercase text-zinc-400 font-bold">Margem</p>
        <p class="font-bold tabular-nums flex items-center gap-1">
          {{ pct(data.margem_orcada_bp) }}
          <template v-if="data.margem_real_bp != null">
            → <span :class="piorou ? 'text-red-600' : 'text-emerald-700'">{{ pct(data.margem_real_bp) }}</span>
            <TrendingDown v-if="piorou" :size="14" class="text-red-600" />
            <TrendingUp v-else :size="14" class="text-emerald-700" />
          </template>
        </p>
      </div>
    </div>
    <table class="w-full text-xs">
      <thead>
        <tr class="text-zinc-400 uppercase text-[10px]">
          <th class="text-left py-1 font-bold">Material / serviço</th>
          <th class="text-right py-1 font-bold">Separado</th>
          <th class="text-right py-1 font-bold">Orçado</th>
          <th class="text-right py-1 font-bold">Real</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-zinc-100">
        <tr v-for="i in data.insumos" :key="i.produto_id">
          <td class="py-1">{{ i.descricao }}</td>
          <td class="py-1 text-right tabular-nums">{{ i.separada }} / {{ i.quantidade }}</td>
          <td class="py-1 text-right tabular-nums">{{ formatCurrency(i.custo_orcado) }}</td>
          <td class="py-1 text-right tabular-nums">{{ i.custo_real != null ? formatCurrency(i.custo_real) : '—' }}</td>
        </tr>
        <tr v-for="t in data.terceirizados" :key="t.movel_id">
          <td class="py-1">{{ t.nome }} <span class="text-zinc-400">(terceirizado)</span></td>
          <td class="py-1 text-right text-zinc-400">—</td>
          <td class="py-1 text-right tabular-nums">{{ formatCurrency(t.custo_orcado) }}</td>
          <td class="py-1 text-right tabular-nums">{{ t.custo_real != null ? formatCurrency(t.custo_real) : '—' }}</td>
        </tr>
      </tbody>
    </table>
    <p class="text-[11px] text-zinc-400">
      O real conta as chapas inteiras que saíram; a sobra do corte continua na prateleira e entra no próximo inventário.
    </p>
  </div>
</template>
