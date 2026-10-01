<script setup lang="ts">
/**
 * @fileoverview O extrato de comissão de uma pessoa, na tela e no papel.
 *
 * Vendas e serviços do período, cada linha com a sua parte da comissão, e o
 * total IGUAL ao da folha de comissão: o backend pega o total da folha e o
 * reparte pelas linhas, então a soma do papel nunca discorda da folha.
 *
 * Aberto pelo ícone de cada linha do Ranking. Só o Master chega aqui — o
 * backend responde 403 para os demais, e a seção inteira vive dentro do
 * `v-if="isMaster"` da tela de relatórios.
 */
import { computed, nextTick, ref, toRef } from 'vue';
import { Printer, FileText, ShoppingCart, Wrench, AlertTriangle, CheckCircle2 } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { imprimirComPagina } from '@/shared/utils/print.utils';

import { useExtratoFuncionarioQuery } from '../composables/useExtratoFuncionarioQuery';
import ExtratoFuncionarioPrint from './ExtratoFuncionarioPrint.vue';

const props = defineProps<{
  isOpen: boolean;
  funcionarioId: number | null;
  inicio: string;
  fim: string;
}>();

const emit = defineEmits<{ (e: 'close'): void }>();

const { data, isLoading, isError } = useExtratoFuncionarioQuery(
  toRef(props, 'funcionarioId'),
  toRef(props, 'inicio'),
  toRef(props, 'fim'),
);

const temVendas = computed(() => (data.value?.vendas.length ?? 0) > 0);
const temServicos = computed(() => (data.value?.itens.length ?? 0) > 0);
const temAlgo = computed(() => temVendas.value || temServicos.value);

/**
 * Loja que lança a peça como item separado nunca preenche `custo` no serviço —
 * ali mão de obra e valor são o mesmo número, e mostrar as duas colunas seria
 * repetir a informação. As colunas só nascem quando há peça embutida em alguma
 * linha.
 */
const temPecaEmbutida = computed(
  () => (data.value?.itens ?? []).some((i) => (i.custo ?? 0) > 0),
);

/** Meta só conta no modo "meta" e com meta definida — igual à folha. */
const usaMeta = computed(() => data.value?.comissao_modo === 'meta' && !!data.value?.meta_mensal);

/** 500 → "5%", 550 → "5,5%". Sem taxa no cadastro → null. */
function pct(bp: number | null | undefined): string | null {
  if (bp == null) return null;
  return `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`;
}

/** "12/08" — o ano já está no cabeçalho do período. */
function diaMes(iso: string): string {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}

function dataLonga(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function fmtQtd(q: number): string {
  return Number.isInteger(q) ? String(q) : q.toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}

/**
 * Impressão A4 — o mesmo fluxo da folha de comissão, incluindo o fallback.
 *
 * O `afterprint` é quem devolve a tela ao normal, mas ele não dispara em todo
 * cenário (diálogo cancelado de certas formas, impressora virtual). O timeout de
 * 60s existe para a folha não ficar montada para sempre quando isso acontece.
 */
const mostrarFolha = ref(false);
async function imprimir() {
  if (!data.value) return;
  mostrarFolha.value = true;
  await nextTick();
  let fallback: ReturnType<typeof setTimeout>;
  const limpar = () => {
    mostrarFolha.value = false;
    window.removeEventListener('afterprint', limpar);
    clearTimeout(fallback);
  };
  window.addEventListener('afterprint', limpar);
  fallback = setTimeout(limpar, 60000);
  imprimirComPagina('A4');
}
</script>

<template>
  <BaseModal
    :is-open="props.isOpen"
    :title="data?.funcionario_nome ? `Extrato de comissão — ${data.funcionario_nome}` : 'Extrato de comissão'"
    :subtitle="data ? `Vendas e serviços de ${dataLonga(data.inicio)} a ${dataLonga(data.fim)}` : 'Vendas e serviços do período'"
    size="3xl"
    @close="emit('close')"
  >
    <ExtratoFuncionarioPrint v-if="mostrarFolha && data" :extrato="data" />

    <div v-if="isError" class="p-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl">
      Não foi possível carregar o extrato. Tente novamente.
    </div>

    <div v-else-if="isLoading" class="py-10 text-center text-sm text-slate-400">Carregando…</div>

    <template v-else-if="data">
      <!-- Resumo: o número que a pessoa quer saber vem primeiro. -->
      <div class="flex flex-wrap items-stretch gap-3 mb-4">
        <div class="rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-3 min-w-44">
          <p class="text-[10px] font-bold uppercase tracking-widest text-emerald-700">Comissão do período</p>
          <p class="text-2xl font-bold text-emerald-700 tabular-nums">{{ formatCurrency(data.comissao_total) }}</p>
        </div>
        <div class="rounded-xl bg-slate-50 border border-slate-200 px-4 py-3">
          <p class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Vendas</p>
          <p class="text-lg font-bold text-slate-800 tabular-nums">{{ formatCurrency(data.total_vendas) }}</p>
          <p class="text-[11px] text-slate-500">{{ data.qtd_vendas }} venda(s)</p>
        </div>
        <div class="rounded-xl bg-slate-50 border border-slate-200 px-4 py-3">
          <p class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Serviços</p>
          <p class="text-lg font-bold text-slate-800 tabular-nums">{{ formatCurrency(data.valor_total) }}</p>
          <p class="text-[11px] text-slate-500">{{ data.qtd_servicos }} serviço(s) em {{ data.qtd_os }} OS</p>
        </div>
        <button
          type="button"
          :disabled="!temAlgo"
          class="ml-auto self-center inline-flex items-center gap-1.5 h-9 px-3 rounded-lg bg-brand-primary text-white text-xs font-semibold hover:bg-brand-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          @click="imprimir"
        >
          <Printer :size="14" /> Imprimir extrato
        </button>
      </div>

      <!-- Como foi calculado: a conta aberta, para a pessoa refazer. -->
      <div v-if="temAlgo" class="rounded-xl border border-slate-200 p-3 mb-4 text-sm space-y-1.5">
        <p class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Como foi calculado</p>
        <div v-if="temVendas" class="flex flex-wrap justify-between gap-2">
          <span class="text-slate-600">
            Vendas: <strong>{{ pct(data.percentual_venda) ?? 'sem percentual' }}</strong> sobre
            {{ formatCurrency(data.base_vendas) }} de margem
          </span>
          <span class="font-semibold text-slate-800 tabular-nums">{{ formatCurrency(data.comissao_vendas) }}</span>
        </div>
        <div v-if="temServicos" class="flex flex-wrap justify-between gap-2">
          <span class="text-slate-600">
            Serviços: <strong>{{ pct(data.percentual_servico) ?? 'sem percentual' }}</strong> sobre
            {{ formatCurrency(data.base_servicos) }} de mão de obra
          </span>
          <span class="font-semibold text-slate-800 tabular-nums">{{ formatCurrency(data.comissao_servico) }}</span>
        </div>
        <p
          v-if="usaMeta && !data.comissao_liberada"
          class="flex items-start gap-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2"
        >
          <AlertTriangle :size="14" class="shrink-0 mt-px" />
          Meta de {{ formatCurrency(data.meta_mensal ?? 0) }} não atingida
          ({{ (data.meta_atingida_percentual ?? 0).toLocaleString('pt-BR') }}%): a comissão só é liberada ao bater a meta.
        </p>
        <p v-else-if="usaMeta" class="flex items-center gap-1.5 text-xs text-emerald-700">
          <CheckCircle2 :size="14" /> Meta de {{ formatCurrency(data.meta_mensal ?? 0) }} atingida
          ({{ (data.meta_atingida_percentual ?? 0).toLocaleString('pt-BR') }}%).
        </p>
        <p class="text-[11px] text-slate-400">
          Margem = valor da venda menos juros do cartão e custo das mercadorias. Mão de obra = valor do serviço menos a peça.
        </p>
      </div>

      <div v-if="!temAlgo" class="py-10 text-center">
        <FileText :size="28" class="mx-auto text-slate-300" />
        <p class="mt-2 text-sm text-slate-500">Nenhuma venda nem serviço finalizado neste período.</p>
      </div>

      <!-- Vendas -->
      <section v-if="temVendas" class="mb-5">
        <h4 class="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-500 mb-1.5">
          <ShoppingCart :size="13" /> Vendas
        </h4>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-[11px] uppercase tracking-wide text-slate-400 border-b border-slate-200">
                <th class="py-2 pr-3 text-left font-medium">Data</th>
                <th class="py-2 px-3 text-left font-medium">Venda</th>
                <th class="py-2 px-3 text-left font-medium">Cliente</th>
                <th class="py-2 px-3 text-right font-medium">Valor</th>
                <th class="py-2 px-3 text-right font-medium">Margem</th>
                <th class="py-2 pl-3 text-right font-medium">Comissão</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in data.vendas" :key="v.venda_id" class="border-b border-slate-100 last:border-0">
                <td class="py-2 pr-3 text-slate-500 tabular-nums">{{ diaMes(v.data) }}</td>
                <td class="py-2 px-3 text-slate-700 font-medium">{{ v.numero }}</td>
                <td class="py-2 px-3 text-slate-500">{{ v.cliente || 'Consumidor' }}</td>
                <td class="py-2 px-3 text-right text-slate-500 tabular-nums">{{ formatCurrency(v.valor_total) }}</td>
                <td class="py-2 px-3 text-right tabular-nums" :class="v.base < 0 ? 'text-rose-600' : 'text-slate-600'">
                  {{ formatCurrency(v.base) }}
                  <span v-if="v.base < 0" class="block text-[10px]">abaixo do custo</span>
                </td>
                <td class="py-2 pl-3 text-right font-semibold text-slate-800 tabular-nums">{{ formatCurrency(v.comissao) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="text-xs font-semibold text-slate-600">
                <td colspan="3" class="pt-2 pr-3">Total de vendas</td>
                <td class="pt-2 px-3 text-right tabular-nums">{{ formatCurrency(data.total_vendas) }}</td>
                <td class="pt-2 px-3" />
                <td class="pt-2 pl-3 text-right text-slate-800 tabular-nums">{{ formatCurrency(data.comissao_vendas) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <!-- Serviços -->
      <section v-if="temServicos">
        <h4 class="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-500 mb-1.5">
          <Wrench :size="13" /> Serviços
        </h4>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-[11px] uppercase tracking-wide text-slate-400 border-b border-slate-200">
                <th class="py-2 pr-3 text-left font-medium">Data</th>
                <th class="py-2 px-3 text-left font-medium">OS</th>
                <th class="py-2 px-3 text-left font-medium">Objeto / Cliente</th>
                <th class="py-2 px-3 text-left font-medium">Serviço</th>
                <th class="py-2 px-3 text-right font-medium">Qtd</th>
                <th class="py-2 px-3 text-right font-medium">Valor</th>
                <th v-if="temPecaEmbutida" class="py-2 px-3 text-right font-medium">Peça</th>
                <th v-if="temPecaEmbutida" class="py-2 px-3 text-right font-medium">Mão de obra</th>
                <th class="py-2 pl-3 text-right font-medium">Comissão</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(i, idx) in data.itens"
                :key="`${i.numero_os}-${idx}`"
                class="border-b border-slate-100 last:border-0"
              >
                <td class="py-2 pr-3 text-slate-500 tabular-nums">{{ diaMes(i.data_finalizacao) }}</td>
                <td class="py-2 px-3 text-slate-700 font-medium">{{ i.numero_os }}</td>
                <td class="py-2 px-3 text-slate-500">
                  <span v-if="i.objeto">{{ i.objeto }}</span>
                  <span v-if="i.objeto && i.cliente"> · </span>
                  <span v-if="i.cliente">{{ i.cliente }}</span>
                  <span v-if="!i.objeto && !i.cliente">—</span>
                </td>
                <td class="py-2 px-3 text-slate-700">{{ i.servico }}</td>
                <td class="py-2 px-3 text-right text-slate-500 tabular-nums">{{ fmtQtd(i.quantidade) }}</td>
                <td class="py-2 px-3 text-right text-slate-500 tabular-nums">{{ formatCurrency(i.valor_total) }}</td>
                <td v-if="temPecaEmbutida" class="py-2 px-3 text-right text-amber-600 tabular-nums">
                  {{ i.custo > 0 ? `− ${formatCurrency(i.custo)}` : '—' }}
                </td>
                <td v-if="temPecaEmbutida" class="py-2 px-3 text-right text-slate-600 tabular-nums">
                  {{ formatCurrency(i.mao_de_obra) }}
                </td>
                <td class="py-2 pl-3 text-right font-semibold text-slate-800 tabular-nums">{{ formatCurrency(i.comissao) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="text-xs font-semibold text-slate-600">
                <td colspan="5" class="pt-2 pr-3">Total de serviços</td>
                <td class="pt-2 px-3 text-right tabular-nums">{{ formatCurrency(data.valor_total) }}</td>
                <td v-if="temPecaEmbutida" class="pt-2 px-3" />
                <td v-if="temPecaEmbutida" class="pt-2 px-3 text-right tabular-nums">{{ formatCurrency(data.total_mao_de_obra) }}</td>
                <td class="pt-2 pl-3 text-right text-slate-800 tabular-nums">{{ formatCurrency(data.comissao_servico) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>
    </template>
  </BaseModal>
</template>
