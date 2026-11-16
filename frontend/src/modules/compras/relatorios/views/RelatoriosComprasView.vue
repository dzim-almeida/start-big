<script setup lang="ts">
/**
 * Relatórios de Compras (fase 5) — as duas perguntas que se faz ao fornecedor:
 * "você entrega no prazo?" e "você subiu o preço?".
 *
 * A fonte são os RECEBIMENTOS de pedido: compra que entrou só pela XML, sem
 * pedido, não tem prazo prometido para medir. Só para quem vê custo (a rota
 * responde 403 a quem tem só a linha Recebimento).
 */
import { computed, ref } from 'vue';
import { PackageCheck, Send, TrendingDown, TrendingUp } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useRelatorioComprasQuery } from '../../shared/composables/useCompras';

function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const hoje = new Date();
const inicio = ref(iso(new Date(hoje.getFullYear(), hoje.getMonth(), 1)));
const fim = ref(iso(hoje));

function esteMes() {
  inicio.value = iso(new Date(hoje.getFullYear(), hoje.getMonth(), 1));
  fim.value = iso(hoje);
}

function ultimosDias(n: number) {
  const de = new Date(hoje);
  de.setDate(de.getDate() - (n - 1));
  inicio.value = iso(de);
  fim.value = iso(hoje);
}

const { data: relatorio, isLoading, isError } = useRelatorioComprasQuery(inicio, fim);
const periodoInvalido = computed(() => !!inicio.value && !!fim.value && inicio.value > fim.value);

function percentual(bp: number): string {
  return `${bp > 0 ? '+' : ''}${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

function pontualidade(noPrazo: number, total: number): string {
  if (!total) return '—';
  return `${noPrazo} de ${total} (${Math.round((noPrazo / total) * 100)}%)`;
}
</script>

<template>
  <div class="flex flex-col gap-6 md:gap-8">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <PageReview title="Relatórios de Compras" description="Prazo e pontualidade dos fornecedores, e quem subiu o preço" />
      <div class="flex flex-wrap items-end gap-3">
        <div class="w-40"><BaseInput v-model="inicio" type="date" label="De" /></div>
        <div class="w-40"><BaseInput v-model="fim" type="date" label="Até" /></div>
        <div class="flex gap-2 pb-0.5 text-xs">
          <button type="button" class="rounded-lg border border-zinc-200 px-3 py-2 hover:bg-zinc-50 cursor-pointer" @click="esteMes">
            Este mês
          </button>
          <button type="button" class="rounded-lg border border-zinc-200 px-3 py-2 hover:bg-zinc-50 cursor-pointer" @click="ultimosDias(90)">
            90 dias
          </button>
        </div>
      </div>
    </div>

    <p v-if="periodoInvalido" class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
      O fim do período é antes do início.
    </p>
    <p v-else-if="isLoading" class="py-10 text-center text-sm text-zinc-400">Montando o relatório…</p>
    <p v-else-if="isError" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      Não foi possível montar o relatório.
    </p>

    <template v-else-if="relatorio">
      <div class="grid gap-3 sm:grid-cols-2">
        <BaseStatsCard :icon="Send" label="Pedidos enviados" :value="String(relatorio.pedidos_enviados)" />
        <BaseStatsCard :icon="PackageCheck" label="Recebido no período" :value="formatCurrency(relatorio.valor_recebido)" />
      </div>

      <!-- Fornecedores -->
      <section class="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <header class="border-b border-zinc-100 px-5 py-3">
          <p class="font-semibold text-zinc-800">Fornecedores</p>
          <p class="text-xs text-zinc-500">Prazo real = do envio do pedido à primeira chegada. "No prazo" = chegou até a data prometida.</p>
        </header>
        <p v-if="!relatorio.por_fornecedor.length" class="px-5 py-8 text-center text-sm text-zinc-400">
          Nenhum pedido enviado ou recebido no período.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-180 text-sm">
            <thead>
              <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                <th class="px-5 py-3">Fornecedor</th>
                <th class="px-5 py-3 text-right">Pedidos</th>
                <th class="px-5 py-3 text-right">Chegadas</th>
                <th class="px-5 py-3 text-right">Recebido</th>
                <th class="px-5 py-3 text-right">Prazo real</th>
                <th class="px-5 py-3 text-right">No prazo</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-100">
              <tr v-for="f in relatorio.por_fornecedor" :key="f.fornecedor_id ?? f.fornecedor_nome">
                <td class="px-5 py-3 font-medium text-zinc-800">{{ f.fornecedor_nome }}</td>
                <td class="px-5 py-3 text-right tabular-nums">{{ f.pedidos_enviados }}</td>
                <td class="px-5 py-3 text-right tabular-nums">{{ f.recebimentos }}</td>
                <td class="px-5 py-3 text-right font-semibold tabular-nums">{{ formatCurrency(f.valor_recebido) }}</td>
                <td class="px-5 py-3 text-right tabular-nums">
                  {{ f.prazo_medio_dias != null ? `${f.prazo_medio_dias.toLocaleString('pt-BR')} dias` : '—' }}
                </td>
                <td
                  class="px-5 py-3 text-right tabular-nums"
                  :class="f.entregas_com_previsao && f.entregas_no_prazo < f.entregas_com_previsao ? 'text-amber-700' : 'text-zinc-700'"
                >
                  {{ pontualidade(f.entregas_no_prazo, f.entregas_com_previsao) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Variação de preço -->
      <section class="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <header class="border-b border-zinc-100 px-5 py-3">
          <p class="font-semibold text-zinc-800">Variação de preço</p>
          <p class="text-xs text-zinc-500">Custo por unidade na primeira e na última chegada do período (produtos comprados 2 vezes ou mais).</p>
        </header>
        <p v-if="!relatorio.variacao_precos.length" class="px-5 py-8 text-center text-sm text-zinc-400">
          Nenhum produto recebido mais de uma vez no período.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-180 text-sm">
            <thead>
              <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                <th class="px-5 py-3">Produto</th>
                <th class="px-5 py-3">Último fornecedor</th>
                <th class="px-5 py-3 text-right">Compras</th>
                <th class="px-5 py-3 text-right">De → Para (por un.)</th>
                <th class="px-5 py-3 text-right">Variação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-100">
              <tr v-for="v in relatorio.variacao_precos" :key="v.produto_id">
                <td class="px-5 py-3 text-zinc-800">{{ v.descricao }}</td>
                <td class="px-5 py-3 text-zinc-600">{{ v.fornecedor_nome }}</td>
                <td class="px-5 py-3 text-right tabular-nums">{{ v.compras }}</td>
                <td class="px-5 py-3 text-right tabular-nums text-zinc-600">
                  {{ formatCurrency(Math.round(v.primeiro_custo_unidade)) }} → {{ formatCurrency(Math.round(v.ultimo_custo_unidade)) }}
                </td>
                <td class="px-5 py-3 text-right">
                  <span
                    class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums"
                    :class="v.variacao_bp > 0 ? 'bg-rose-50 text-rose-700' : v.variacao_bp < 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-zinc-100 text-zinc-500'"
                  >
                    <TrendingUp v-if="v.variacao_bp > 0" :size="11" />
                    <TrendingDown v-else-if="v.variacao_bp < 0" :size="11" />
                    {{ percentual(v.variacao_bp) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
