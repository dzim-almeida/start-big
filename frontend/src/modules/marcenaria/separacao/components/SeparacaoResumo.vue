<script setup lang="ts">
/**
 * @component SeparacaoResumo
 * @description Orçado × real por produto (Spec 10B D11; 10A D15), recolhido
 * por padrão no fim da aba.
 *
 * É QUANTIDADE, não preço: todos veem. É o número que diz se a perda
 * configurada está certa ("+12% sobre o orçado" em todas as obras = a perda
 * está baixa). Só entram os produtos que já tiveram retirada.
 */
import { computed, ref } from 'vue';
import { ChevronDown } from 'lucide-vue-next';

import type { LinhaSeparacao } from '../schemas/separacao.schema';
import { diferencaTexto, quantidadeComUnidade } from '../utils/quantidades';

const props = defineProps<{ linhas: LinhaSeparacao[] }>();

const aberto = ref(false);

/** Só o que tem orçado e retirado (antes de retirar não há "real"). */
const comparaveis = computed(() => props.linhas.filter((l) => l.diferenca_bp != null && l.planejado_milesimos != null));
const acima = computed(() => comparaveis.value.filter((l) => (l.diferenca_bp ?? 0) > 0).length);

const titulo = computed(() => {
  if (!acima.value) return 'Orçado × real';
  return `Orçado × real (${acima.value} ${acima.value === 1 ? 'produto acima' : 'produtos acima'} do orçado)`;
});
</script>

<template>
  <section v-if="comparaveis.length" class="rounded-xl border border-zinc-200" data-testid="orcado-real">
    <button
      type="button"
      class="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-zinc-700 cursor-pointer"
      :aria-expanded="aberto"
      @click="aberto = !aberto"
    >
      {{ titulo }}
      <ChevronDown :size="16" class="text-zinc-400 transition-transform" :class="aberto ? '' : '-rotate-90'" />
    </button>
    <table v-if="aberto" class="w-full border-t border-zinc-100 text-sm">
      <thead class="text-left text-xs text-zinc-500">
        <tr>
          <th class="px-4 py-2 font-medium">Produto</th>
          <th class="px-4 py-2 text-right font-medium">Orçado</th>
          <th class="px-4 py-2 text-right font-medium">Retirado</th>
          <th class="px-4 py-2 text-right font-medium">Diferença</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-zinc-100">
        <tr v-for="linha in comparaveis" :key="linha.item_id">
          <td class="px-4 py-2 text-zinc-800">{{ linha.descricao }}</td>
          <td class="px-4 py-2 text-right tabular-nums text-zinc-600">{{ quantidadeComUnidade(linha.planejado_milesimos!, linha.unidade) }}</td>
          <td class="px-4 py-2 text-right tabular-nums text-zinc-600">{{ quantidadeComUnidade(linha.separada_milesimos, linha.unidade) }}</td>
          <td
            class="px-4 py-2 text-right tabular-nums font-medium"
            :class="(linha.diferenca_bp ?? 0) > 0 ? 'text-amber-700' : 'text-zinc-700'"
            :data-testid="`diferenca-${linha.item_id}`"
          >
            {{ diferencaTexto(linha.diferenca_bp!) }}
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
