<script setup lang="ts">
/**
 * Vendas por regra de preço por quantidade (plano de embalagens, fase 6).
 *
 * Responde a pergunta de quem ligou a regra: "quanto deixei de cobrar com o
 * preço de fardo, e quanto vendi com ele?". O abatimento junta as duas formas
 * da regra — R1/R3 como desconto da linha, R2 como preço mais baixo — para o
 * dono comparar as três na mesma régua.
 */
import { computed, toRef } from 'vue';
import { Tags, Download } from 'lucide-vue-next';

import { formatCurrency, formatCentsToInput } from '@/shared/utils/finance';
import { saveCsv } from '@/shared/utils/csv';
import { useToast } from '@/shared/composables/useToast';
import { useRegrasPrecoQuery } from '../composables/useRegrasPrecoQuery';
import type { RegraPrecoCodigo } from '../schemas/regrasPreco.schema';

const props = defineProps<{ inicio: string; fim: string }>();

const { data } = useRegrasPrecoQuery(toRef(props, 'inicio'), toRef(props, 'fim'));
const toast = useToast();

const porRegra = computed(() => data.value?.por_regra ?? []);
const porProduto = computed(() => data.value?.por_produto ?? []);

// O mesmo nome que o dono vê em Configurações › Regras de Vendas.
const NOME_REGRA: Record<RegraPrecoCodigo, string> = {
  R1: 'Preço de embalagem nas avulsas',
  R2: 'A partir de N unidades',
  R3: 'Leve X, pague Y',
};

const COR_REGRA: Record<RegraPrecoCodigo, string> = {
  R1: 'bg-blue-50 text-blue-700',
  R2: 'bg-emerald-50 text-emerald-700',
  R3: 'bg-amber-50 text-amber-700',
};

async function exportar() {
  const d = data.value;
  if (!d) return;
  const linhas = d.por_produto.map((i) => [
    i.regra,
    NOME_REGRA[i.regra],
    i.nome,
    i.sku ?? '',
    String(i.qtd_vendas),
    String(i.unidades),
    formatCentsToInput(i.faturamento),
    formatCentsToInput(i.abatimento),
  ]);
  const caminho = await saveCsv(
    `vendas_por_regra_${d.inicio}_a_${d.fim}.csv`,
    ['Regra', 'Descrição', 'Produto', 'SKU', 'Vendas', 'Unidades', 'Faturamento (R$)', 'Deixou de cobrar (R$)'],
    linhas,
  );
  if (caminho) toast.success(`Relatório salvo em: ${caminho}`);
}
</script>

<template>
  <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2">
        <Tags :size="15" class="text-brand-primary" /> Vendas por regra de preço
      </h3>
      <button
        v-if="porProduto.length"
        type="button"
        class="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:border-brand-primary hover:text-brand-primary transition-colors cursor-pointer"
        @click="exportar"
      >
        <Download :size="14" /> Exportar
      </button>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
        <span class="text-[10px] uppercase text-slate-400 font-semibold tracking-wide">Vendas com regra</span>
        <p class="text-base font-bold text-slate-700 leading-tight tabular-nums">{{ data?.qtd_vendas ?? 0 }}</p>
      </div>
      <div class="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
        <span class="text-[10px] uppercase text-slate-400 font-semibold tracking-wide">Faturado com regra</span>
        <p class="text-base font-bold text-slate-700 leading-tight tabular-nums">{{ formatCurrency(data?.faturamento ?? 0) }}</p>
      </div>
      <div class="rounded-lg border border-amber-100 bg-amber-50/60 p-3">
        <span class="text-[10px] uppercase text-amber-500 font-semibold tracking-wide">Deixou de cobrar</span>
        <p class="text-base font-bold text-amber-700 leading-tight tabular-nums">{{ formatCurrency(data?.abatimento ?? 0) }}</p>
        <span class="text-[11px] text-slate-400">frente ao preço cheio da unidade</span>
      </div>
    </div>

    <template v-if="porProduto.length">
      <!-- Por regra -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div v-for="r in porRegra" :key="r.regra" class="rounded-lg border border-slate-100 p-3">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="rounded-full text-[11px] font-bold px-2 py-0.5" :class="COR_REGRA[r.regra]">{{ r.regra }}</span>
            <span class="text-xs font-semibold text-slate-600">{{ NOME_REGRA[r.regra] }}</span>
          </div>
          <div class="flex justify-between text-xs text-slate-500">
            <span>{{ r.qtd_vendas }} venda(s) · {{ r.unidades }} un</span>
            <span class="tabular-nums">{{ formatCurrency(r.faturamento) }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-slate-400">deixou de cobrar</span>
            <span class="text-amber-700 font-semibold tabular-nums">− {{ formatCurrency(r.abatimento) }}</span>
          </div>
        </div>
      </div>

      <!-- Por produto -->
      <div class="overflow-x-auto">
        <table class="w-full text-sm min-w-150">
          <thead>
            <tr class="text-[11px] uppercase tracking-wide text-slate-400 border-b border-slate-200">
              <th class="py-2 pr-2 font-semibold text-center w-12">Regra</th>
              <th class="py-2 px-3 font-semibold text-left">Produto</th>
              <th class="py-2 px-2 font-semibold text-right">Vendas</th>
              <th class="py-2 px-2 font-semibold text-right">Unidades</th>
              <th class="py-2 px-3 font-semibold text-right">Faturamento</th>
              <th class="py-2 pl-2 font-semibold text-right">Deixou de cobrar</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="i in porProduto"
              :key="`${i.regra}-${i.produto_id}`"
              class="border-b border-slate-100 last:border-0"
            >
              <td class="py-2 pr-2 text-center">
                <span class="inline-block rounded-full text-[11px] font-bold px-2 py-0.5" :class="COR_REGRA[i.regra]">{{ i.regra }}</span>
              </td>
              <td class="py-2 px-3 text-slate-700 font-medium">
                {{ i.nome }}
                <span v-if="i.sku" class="text-[11px] text-slate-400">· {{ i.sku }}</span>
              </td>
              <td class="py-2 px-2 text-right text-slate-500 tabular-nums">{{ i.qtd_vendas }}</td>
              <td class="py-2 px-2 text-right text-slate-500 tabular-nums">{{ i.unidades }}</td>
              <td class="py-2 px-3 text-right text-slate-600 tabular-nums">{{ formatCurrency(i.faturamento) }}</td>
              <td class="py-2 pl-2 text-right text-amber-700 tabular-nums">− {{ formatCurrency(i.abatimento) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
    <div v-else class="py-6 text-center text-xs text-slate-400">
      Nenhuma venda com regra de preço no período.
    </div>
  </div>
</template>
