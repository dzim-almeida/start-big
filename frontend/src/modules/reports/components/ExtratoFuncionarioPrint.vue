<script setup lang="ts">
/**
 * @fileoverview Extrato de comissão imprimível (A4), no mesmo padrão da folha
 * de comissão. Renderizado só em print (`hidden print:block`) e teleportado para
 * o body para o print-a4.css global isolar só o `.print-container`.
 *
 * É o papel que o dono entrega em mãos, então ele responde sozinho às perguntas
 * que o funcionário vai fazer: o que eu vendi e fiz, em qual venda/OS, sobre
 * quanto foi a comissão e quanto deu. O total é o da folha de comissão (o
 * backend reparte o total da folha pelas linhas), e a linha de assinatura fecha
 * a conferência — é o "recebi e conferi" dos sistemas de folha.
 */
import { computed } from 'vue';

import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { RelatorioExtratoFuncionario } from '../schemas/extratoFuncionario.schema';

const props = defineProps<{ extrato: RelatorioExtratoFuncionario }>();

const { companyInfo } = useCompanyPrintInfo();

function fmtData(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}
const periodo = computed(() => `${fmtData(props.extrato.inicio)} a ${fmtData(props.extrato.fim)}`);

/** "12/08" — no corpo da tabela o ano é ruído: ele já está no período do topo. */
function diaMes(iso: string): string {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}

/**
 * Quantidade sem casa decimal quando é inteira.
 *
 * Serviço costuma ser 1, mas a coluna é `Float` — serigrafia trabalha com
 * quantidade fracionária. "1,00" numa folha de oficina é ruído; "2,5" numa de
 * serigrafia é a informação.
 */
function fmtQtd(q: number): string {
  return Number.isInteger(q) ? String(q) : q.toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}

function pct(bp: number | null | undefined): string {
  if (bp == null) return 'sem %';
  return `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`;
}

const usaMeta = computed(() => props.extrato.comissao_modo === 'meta' && !!props.extrato.meta_mensal);
const th = 'border border-neutral-300 px-2 py-1 font-bold uppercase text-[10px]';
const td = 'border border-neutral-300 px-2 py-1';
</script>

<template>
  <Teleport to="body">
    <div class="print-container hidden print:block bg-white text-black font-sans leading-tight">
      <!-- Cabeçalho da empresa -->
      <header class="flex justify-between items-start gap-4 border border-neutral-800 rounded-lg p-4 mb-4">
        <div class="flex items-start gap-3">
          <div class="w-20 h-20 border border-neutral-300 rounded-lg flex items-center justify-center shrink-0 overflow-hidden">
            <img v-if="companyInfo.logo" :src="companyInfo.logo" alt="Logo" class="w-full h-full object-contain p-1" />
          </div>
          <div>
            <h1 class="text-lg font-black text-neutral-900 uppercase tracking-tight">{{ companyInfo.nome }}</h1>
            <p v-if="companyInfo.razaoSocial" class="text-[10px] uppercase font-bold text-neutral-600">{{ companyInfo.razaoSocial }}</p>
            <p v-if="companyInfo.endereco" class="text-xs text-neutral-800 mt-1">{{ companyInfo.endereco }}</p>
            <p v-if="companyInfo.cnpj" class="text-xs text-neutral-800">
              {{ companyInfo.labelDocumento || 'CNPJ' }}: {{ companyInfo.cnpj }}
            </p>
          </div>
        </div>
        <div class="text-right">
          <div class="bg-neutral-900 text-white px-3 py-1.5 rounded-lg">
            <p class="text-[10px] font-bold uppercase tracking-wider">Extrato de Comissão</p>
          </div>
          <p class="text-[10px] font-bold text-neutral-600 uppercase mt-2">Período</p>
          <p class="text-sm font-bold text-neutral-900">{{ periodo }}</p>
        </div>
      </header>

      <!-- Quem e quanto -->
      <div class="flex justify-between items-center py-2 px-3 mb-4 border-y-2 border-neutral-200 bg-neutral-50">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Funcionário</p>
          <h2 class="text-lg font-black text-neutral-900 uppercase tracking-widest">{{ extrato.funcionario_nome }}</h2>
        </div>
        <div class="text-right">
          <p class="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Comissão do período</p>
          <p class="text-xl font-black text-neutral-900 tabular-nums">{{ formatCurrency(extrato.comissao_total) }}</p>
        </div>
      </div>

      <!-- Vendas -->
      <template v-if="extrato.vendas.length">
        <h3 class="text-[11px] font-black uppercase tracking-wider mb-1">Vendas</h3>
        <table class="w-full border-collapse text-xs mb-4">
          <thead>
            <tr class="bg-neutral-100">
              <th :class="[th, 'text-left']">Data</th>
              <th :class="[th, 'text-left']">Venda</th>
              <th :class="[th, 'text-left']">Cliente</th>
              <th :class="[th, 'text-right']">Valor</th>
              <th :class="[th, 'text-right']">Margem</th>
              <th :class="[th, 'text-right']">Comissão</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="v in extrato.vendas" :key="v.venda_id">
              <td :class="[td, 'tabular-nums']">{{ diaMes(v.data) }}</td>
              <td :class="[td, 'font-medium']">{{ v.numero }}</td>
              <td :class="td">{{ v.cliente || 'Consumidor' }}</td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(v.valor_total) }}</td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(v.base) }}</td>
              <td :class="[td, 'text-right tabular-nums font-bold']">{{ formatCurrency(v.comissao) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-neutral-100 font-bold">
              <td colspan="3" :class="[td, 'uppercase text-[11px]']">
                {{ extrato.qtd_vendas }} venda(s) · {{ pct(extrato.percentual_venda) }} sobre {{ formatCurrency(extrato.base_vendas) }} de margem
              </td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(extrato.total_vendas) }}</td>
              <td :class="td" />
              <td :class="[td, 'text-right tabular-nums text-sm']">{{ formatCurrency(extrato.comissao_vendas) }}</td>
            </tr>
          </tfoot>
        </table>
      </template>

      <!-- Serviços -->
      <template v-if="extrato.itens.length">
        <h3 class="text-[11px] font-black uppercase tracking-wider mb-1">Serviços</h3>
        <table class="w-full border-collapse text-xs mb-4">
          <thead>
            <tr class="bg-neutral-100">
              <th :class="[th, 'text-left']">Data</th>
              <th :class="[th, 'text-left']">OS</th>
              <th :class="[th, 'text-left']">Objeto / Cliente</th>
              <th :class="[th, 'text-left']">Serviço</th>
              <th :class="[th, 'text-right']">Qtd</th>
              <th :class="[th, 'text-right']">Valor</th>
              <th :class="[th, 'text-right']">Mão de obra</th>
              <th :class="[th, 'text-right']">Comissão</th>
            </tr>
          </thead>
          <tbody>
            <!--
              A OS e o objeto se repetem em cada linha, em vez de célula vazia.
              O papel é conferido item a item, e uma célula em branco obriga quem lê
              a subir para saber de qual OS aquilo é.
            -->
            <tr v-for="(i, idx) in extrato.itens" :key="`${i.numero_os}-${idx}`">
              <td :class="[td, 'tabular-nums']">{{ diaMes(i.data_finalizacao) }}</td>
              <td :class="[td, 'font-medium']">{{ i.numero_os }}</td>
              <td :class="td">
                <span v-if="i.objeto">{{ i.objeto }}</span>
                <span v-if="i.objeto && i.cliente"> · </span>
                <span v-if="i.cliente">{{ i.cliente }}</span>
                <span v-if="!i.objeto && !i.cliente" class="text-neutral-400">—</span>
              </td>
              <td :class="td">{{ i.servico }}</td>
              <td :class="[td, 'text-right tabular-nums']">{{ fmtQtd(i.quantidade) }}</td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(i.valor_total) }}</td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(i.mao_de_obra) }}</td>
              <td :class="[td, 'text-right tabular-nums font-bold']">{{ formatCurrency(i.comissao) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-neutral-100 font-bold">
              <td colspan="5" :class="[td, 'uppercase text-[11px]']">
                {{ extrato.qtd_servicos }} serviço(s) em {{ extrato.qtd_os }} OS · {{ pct(extrato.percentual_servico) }} sobre
                {{ formatCurrency(extrato.base_servicos) }} de mão de obra
              </td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(extrato.valor_total) }}</td>
              <td :class="[td, 'text-right tabular-nums']">{{ formatCurrency(extrato.total_mao_de_obra) }}</td>
              <td :class="[td, 'text-right tabular-nums text-sm']">{{ formatCurrency(extrato.comissao_servico) }}</td>
            </tr>
          </tfoot>
        </table>
      </template>

      <p v-if="!extrato.vendas.length && !extrato.itens.length" class="py-6 text-center text-neutral-500 text-sm">
        Nenhuma venda nem serviço finalizado neste período.
      </p>

      <!-- Resumo final -->
      <table class="ml-auto border-collapse text-xs mb-3">
        <tbody>
          <tr v-if="extrato.vendas.length">
            <td class="px-3 py-1 text-right">Comissão de vendas</td>
            <td class="px-3 py-1 text-right tabular-nums">{{ formatCurrency(extrato.comissao_vendas) }}</td>
          </tr>
          <tr v-if="extrato.itens.length">
            <td class="px-3 py-1 text-right">Comissão de serviços</td>
            <td class="px-3 py-1 text-right tabular-nums">{{ formatCurrency(extrato.comissao_servico) }}</td>
          </tr>
          <tr class="border-t-2 border-neutral-800 font-black">
            <td class="px-3 py-1.5 text-right uppercase">Total a receber</td>
            <td class="px-3 py-1.5 text-right tabular-nums text-sm">{{ formatCurrency(extrato.comissao_total) }}</td>
          </tr>
        </tbody>
      </table>

      <p v-if="usaMeta" class="text-[10px] text-neutral-700 mb-2">
        Meta do período: {{ formatCurrency(extrato.meta_mensal ?? 0) }} —
        {{ extrato.comissao_liberada ? 'atingida' : 'não atingida' }}
        ({{ (extrato.meta_atingida_percentual ?? 0).toLocaleString('pt-BR') }}%).
        <template v-if="!extrato.comissao_liberada">A comissão só é liberada ao bater a meta.</template>
      </p>
      <p class="text-[10px] text-neutral-600 leading-snug">
        Margem = valor da venda menos juros do cartão e custo das mercadorias. Mão de obra = valor do
        serviço menos a peça aplicada. O total confere com a folha de comissão do período.
      </p>

      <!-- Conferência -->
      <div class="grid grid-cols-2 gap-10 mt-12 text-[10px] text-neutral-700">
        <div class="border-t border-neutral-800 pt-1 text-center">
          {{ extrato.funcionario_nome }} — conferi e estou de acordo
        </div>
        <div class="border-t border-neutral-800 pt-1 text-center">Responsável pela loja</div>
      </div>

      <PrintFooter />
    </div>
  </Teleport>
</template>
