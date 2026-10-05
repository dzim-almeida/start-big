<script setup lang="ts">
/**
 * @fileoverview A proposta que vai para o cliente (A4): ambientes, móveis com
 * medida e preço, total, sinal e validade.
 *
 * NUNCA sai aqui: lista de material e custo — é o segredo da fábrica e não é o
 * que o cliente compra. Mesmo padrão da folha de comissão: só renderiza na
 * impressão e é teleportada para o body (print-a4.css isola o .print-container).
 */
import { computed } from 'vue';

import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { formatDataPura } from '@/shared/utils/date.utils';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';

import type { OrcamentoRead } from '../types/fabrica.types';

const props = defineProps<{
  orcamento: OrcamentoRead;
  cliente: string;
  projeto: string;
}>();

const { companyInfo } = useCompanyPrintInfo();

const sinalPercentual = computed(() =>
  (props.orcamento.sinal_bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 }),
);
</script>

<template>
  <Teleport to="body">
    <div class="print-container hidden print:block bg-white text-black font-sans leading-tight">
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
            <p class="text-[10px] font-bold uppercase tracking-wider">Proposta</p>
          </div>
          <p class="text-sm font-bold text-neutral-900 mt-2">{{ orcamento.numero_os }} · versão {{ orcamento.versao }}</p>
          <p v-if="orcamento.validade" class="text-[11px] text-neutral-700">
            Válida até {{ formatDataPura(orcamento.validade) }}
          </p>
        </div>
      </header>

      <section class="border border-neutral-300 rounded-lg p-3 mb-4 text-xs grid grid-cols-2 gap-2">
        <p><span class="font-bold uppercase text-[10px] text-neutral-600">Cliente</span><br />{{ cliente }}</p>
        <p><span class="font-bold uppercase text-[10px] text-neutral-600">Projeto</span><br />{{ projeto }}</p>
      </section>

      <table class="w-full border-collapse text-xs mb-3">
        <thead>
          <tr class="bg-neutral-100 text-neutral-800">
            <th class="border border-neutral-300 px-2 py-1.5 text-left font-bold uppercase text-[10px]">Móvel</th>
            <th class="border border-neutral-300 px-2 py-1.5 text-left font-bold uppercase text-[10px] w-32">Medidas (mm)</th>
            <th class="border border-neutral-300 px-2 py-1.5 text-right font-bold uppercase text-[10px] w-28">Valor</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="amb in orcamento.ambientes" :key="amb.id">
            <tr class="bg-neutral-50">
              <td colspan="3" class="border border-neutral-300 px-2 py-1 font-black uppercase text-[10px] tracking-wider">
                {{ amb.nome }}
              </td>
            </tr>
            <tr v-for="mov in amb.moveis" :key="mov.id">
              <td class="border border-neutral-300 px-2 py-1">{{ mov.nome }}</td>
              <td class="border border-neutral-300 px-2 py-1 tabular-nums">{{ mov.medidas || '—' }}</td>
              <td class="border border-neutral-300 px-2 py-1 text-right tabular-nums">{{ formatCurrency(mov.preco_venda) }}</td>
            </tr>
          </template>
        </tbody>
        <tfoot>
          <tr class="bg-neutral-100">
            <td colspan="2" class="border border-neutral-300 px-2 py-2 text-right font-black uppercase">Total</td>
            <td class="border border-neutral-300 px-2 py-2 text-right font-black tabular-nums">{{ formatCurrency(orcamento.total) }}</td>
          </tr>
          <tr v-if="orcamento.sinal_bp > 0">
            <td colspan="2" class="border border-neutral-300 px-2 py-1.5 text-right font-bold">
              Sinal para iniciar ({{ sinalPercentual }}%)
            </td>
            <td class="border border-neutral-300 px-2 py-1.5 text-right font-bold tabular-nums">{{ formatCurrency(orcamento.sinal_valor) }}</td>
          </tr>
        </tfoot>
      </table>

      <p v-if="orcamento.observacao" class="text-xs text-neutral-800 whitespace-pre-line mb-6">{{ orcamento.observacao }}</p>

      <div class="grid grid-cols-2 gap-10 mt-16 text-xs">
        <div class="text-center">
          <div class="border-t border-neutral-700 pt-1 text-neutral-700">{{ companyInfo.nome }}</div>
        </div>
        <div class="text-center">
          <div class="border-t border-neutral-700 pt-1 text-neutral-700">De acordo — {{ cliente }}</div>
        </div>
      </div>

      <PrintFooter />
    </div>
  </Teleport>
</template>

<style>
@import '@/shared/components/print/styles/print-a4.css';
</style>
