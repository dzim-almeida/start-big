<script setup lang="ts">
/**
 * Receita para o contador — a separação que ele faz no PGDAS-D.
 *
 * No Simples, a receita de revenda paga menos DAS quando o ICMS já veio pago
 * por substituição (ST) ou o PIS/COFINS é monofásico. Se o contador não
 * separa, a loja paga esses impostos duas vezes. Este bloco entrega a receita
 * já separada, pelo cadastro fiscal de cada produto, e aponta o que está sem
 * classificação para corrigir antes de mandar.
 */
import { computed, toRef } from 'vue';
import { Calculator, Download, AlertTriangle } from 'lucide-vue-next';

import { formatCurrency, formatCentsToInput } from '@/shared/utils/finance';
import { saveCsv } from '@/shared/utils/csv';
import { useToast } from '@/shared/composables/useToast';
import { useContadorQuery } from '../composables/useContadorQuery';
import type { ReceitaGrupoItem } from '../schemas/contador.schema';

const props = defineProps<{ inicio: string; fim: string }>();

const { data } = useContadorQuery(toRef(props, 'inicio'), toRef(props, 'fim'));
const toast = useToast();

const REGIME: Record<number, string> = {
  1: 'Simples Nacional',
  2: 'Simples Nacional — excesso de sublimite',
  3: 'Regime normal',
  4: 'MEI',
};

function nomeGrupo(g: ReceitaGrupoItem): string {
  if (g.icms_st && g.monofasico) return 'Revenda com ICMS-ST e PIS/COFINS monofásico';
  if (g.icms_st) return 'Revenda com ICMS-ST';
  if (g.monofasico) return 'Revenda com PIS/COFINS monofásico';
  return 'Revenda sem ST e sem monofásico';
}

/** As linhas do quadro, na ordem em que o contador lança. */
const linhas = computed(() => {
  const d = data.value;
  if (!d) return [];
  return [
    ...d.mercadoria.map((g) => ({ nome: nomeGrupo(g), valor: g.valor, alerta: false })),
    { nome: 'Mercadoria sem classificação fiscal', valor: d.mercadoria_sem_classificacao, alerta: true },
    { nome: 'Serviços (OS)', valor: d.servicos, alerta: false },
    { nome: 'Frete e juros cobrados do cliente', valor: d.frete_e_juros, alerta: false },
  ].filter((l) => !l.alerta || l.valor > 0);
});

const semClassificacao = computed(() => data.value?.produtos_sem_classificacao ?? []);

async function exportar() {
  const d = data.value;
  if (!d) return;
  const corpo = linhas.value.map((l) => [l.nome, formatCentsToInput(l.valor)]);
  corpo.push(['Total', formatCentsToInput(d.receita_total)]);
  if (semClassificacao.value.length) {
    corpo.push(['', '']);
    corpo.push(['Produtos sem classificação fiscal', '']);
    for (const p of semClassificacao.value) corpo.push([`${p.nome} — ${p.motivo}`, formatCentsToInput(p.valor)]);
  }
  const caminho = await saveCsv(`receita_contador_${d.inicio}_a_${d.fim}.csv`, ['Grupo', 'Receita (R$)'], corpo);
  if (caminho) toast.success(`Relatório salvo em: ${caminho}`);
}
</script>

<template>
  <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-sm font-bold text-slate-700 flex items-center gap-2">
          <Calculator :size="15" class="text-brand-primary" /> Receita para o contador
        </h3>
        <p class="text-xs text-slate-500 mt-0.5">
          Separada como no PGDAS-D, pelo cadastro fiscal de cada produto
          <template v-if="data?.crt"> · {{ REGIME[data.crt] ?? `CRT ${data.crt}` }}</template>
        </p>
      </div>
      <button
        v-if="data"
        type="button"
        class="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:border-brand-primary hover:text-brand-primary transition-colors cursor-pointer"
        @click="exportar"
      >
        <Download :size="14" /> Exportar para o contador
      </button>
    </div>

    <table v-if="data" class="w-full text-sm">
      <tbody>
        <tr v-for="l in linhas" :key="l.nome" class="border-b border-slate-100">
          <td class="py-2 pr-3" :class="l.alerta ? 'text-amber-700 font-medium' : 'text-slate-600'">{{ l.nome }}</td>
          <td class="py-2 text-right tabular-nums" :class="l.alerta ? 'text-amber-700 font-semibold' : 'text-slate-700'">
            {{ formatCurrency(l.valor) }}
          </td>
        </tr>
        <tr>
          <td class="pt-2 pr-3 font-bold text-slate-700">Receita do período</td>
          <td class="pt-2 text-right font-bold text-slate-800 tabular-nums">{{ formatCurrency(data.receita_total) }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Produto sem classificação não é chutado como "normal": um chute
         errado faz a loja pagar ICMS duas vezes sem ninguém ver. -->
    <div
      v-if="semClassificacao.length"
      class="rounded-lg border border-amber-200 bg-amber-50 p-3 space-y-2"
    >
      <p class="flex items-start gap-1.5 text-xs text-amber-800">
        <AlertTriangle :size="14" class="shrink-0 mt-px" />
        <span>
          Estes itens não dizem no cadastro se o ICMS é por substituição tributária. Preencha o
          <strong>CSOSN</strong> (ou o CST) na aba fiscal do produto e o relatório se corrige sozinho,
          inclusive para os meses anteriores.
        </span>
      </p>
      <ul class="space-y-1 max-h-56 overflow-y-auto">
        <li v-for="p in semClassificacao" :key="`${p.produto_id}-${p.nome}`" class="flex justify-between gap-3 text-xs">
          <span class="text-amber-900 truncate">{{ p.nome }} <span class="text-amber-600">· {{ p.motivo }}</span></span>
          <span class="tabular-nums text-amber-900 shrink-0">{{ formatCurrency(p.valor) }}</span>
        </li>
      </ul>
    </div>

    <p class="text-[11px] text-slate-400">
      O grupo vem do cadastro do produto: CSOSN 500 ou CST 60 = ICMS-ST; CST de PIS/COFINS 04 = monofásico.
      Quem confirma se cada produto é mesmo ST no seu estado é o contador.
    </p>
  </div>
</template>
