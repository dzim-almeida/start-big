<script setup lang="ts">
/**
 * @fileoverview O pedido de compra em papel (A4) — para mandar ao fornecedor
 * por e-mail como PDF ("Salvar como PDF" no diálogo de impressão) ou entregar
 * ao vendedor que passa na loja.
 *
 * Mesmo molde das outras folhas A4: `hidden print:block` + Teleport para o
 * body, e o print-a4.css global isola só o `.print-container`.
 *
 * Preço sai só para quem pode vê-lo (D14): o backend já manda nulo, e a folha
 * esconde as colunas em vez de imprimir "—" em todas as linhas.
 */
import { computed } from 'vue';

import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';
import { formatDataPura } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';

import type { PedidoRead } from '../../shared/types/compras.types';

const props = defineProps<{ pedido: PedidoRead }>();

const { companyInfo } = useCompanyPrintInfo();
const comPreco = computed(() => props.pedido.valor_total != null);

const emitidoEm = new Date().toLocaleString('pt-BR', {
  day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
});

function qtd(n: number): string {
  return n.toLocaleString('pt-BR');
}
</script>

<template>
  <Teleport to="body">
    <div class="print-container pedido-compra-folha hidden print:block bg-white text-black font-sans leading-tight">
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
            <p class="text-[10px] font-bold uppercase tracking-wider">Pedido de Compra</p>
          </div>
          <p class="text-xl font-black text-neutral-900 mt-2">{{ pedido.codigo }}</p>
          <p class="text-[10px] text-neutral-600">Emitido em {{ emitidoEm }}</p>
        </div>
      </header>

      <div class="grid grid-cols-3 gap-3 mb-4 text-xs">
        <div class="border border-neutral-300 rounded-lg p-3 col-span-1">
          <p class="text-[10px] font-bold uppercase tracking-wider text-neutral-500">Fornecedor</p>
          <p class="text-sm font-bold text-neutral-900 mt-1">{{ pedido.fornecedor_nome }}</p>
        </div>
        <div class="border border-neutral-300 rounded-lg p-3">
          <p class="text-[10px] font-bold uppercase tracking-wider text-neutral-500">Entrega até</p>
          <p class="text-sm font-bold text-neutral-900 mt-1">{{ formatDataPura(pedido.previsao_entrega, 'A combinar') }}</p>
        </div>
        <div class="border border-neutral-300 rounded-lg p-3">
          <p class="text-[10px] font-bold uppercase tracking-wider text-neutral-500">Pagamento</p>
          <p class="text-sm font-bold text-neutral-900 mt-1">{{ pedido.condicao_pagamento || 'A combinar' }}</p>
        </div>
      </div>

      <table class="w-full border-collapse text-xs tabela-itens">
        <thead>
          <tr class="bg-neutral-100">
            <th class="border border-neutral-300 px-2 py-1 text-left font-bold uppercase text-[10px] w-8">#</th>
            <th class="border border-neutral-300 px-2 py-1 text-left font-bold uppercase text-[10px]">Produto</th>
            <th class="border border-neutral-300 px-2 py-1 text-left font-bold uppercase text-[10px]">Cód. fornecedor</th>
            <th class="border border-neutral-300 px-2 py-1 text-right font-bold uppercase text-[10px]">Qtd.</th>
            <th class="border border-neutral-300 px-2 py-1 text-left font-bold uppercase text-[10px]">Un.</th>
            <th v-if="comPreco" class="border border-neutral-300 px-2 py-1 text-right font-bold uppercase text-[10px]">Preço</th>
            <th v-if="comPreco" class="border border-neutral-300 px-2 py-1 text-right font-bold uppercase text-[10px]">Subtotal</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, i) in pedido.itens" :key="item.id">
            <td class="border border-neutral-300 px-2 py-1 tabular-nums">{{ i + 1 }}</td>
            <td class="border border-neutral-300 px-2 py-1">{{ item.descricao }}</td>
            <td class="border border-neutral-300 px-2 py-1">{{ item.codigo_fornecedor || '' }}</td>
            <td class="border border-neutral-300 px-2 py-1 text-right tabular-nums font-bold">{{ qtd(item.quantidade) }}</td>
            <td class="border border-neutral-300 px-2 py-1">
              {{ item.unidade_compra }}<template v-if="item.fator > 1"> c/ {{ item.fator }}</template>
            </td>
            <td v-if="comPreco" class="border border-neutral-300 px-2 py-1 text-right tabular-nums">
              {{ formatCurrency(item.custo_unitario ?? 0) }}
            </td>
            <td v-if="comPreco" class="border border-neutral-300 px-2 py-1 text-right tabular-nums">
              {{ formatCurrency(item.subtotal ?? 0) }}
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="comPreco" class="mt-3 flex justify-end">
        <dl class="w-64 text-xs">
          <div class="flex justify-between py-0.5"><dt>Itens</dt><dd class="tabular-nums">{{ formatCurrency(pedido.valor_itens ?? 0) }}</dd></div>
          <div v-if="pedido.frete" class="flex justify-between py-0.5"><dt>Frete</dt><dd class="tabular-nums">{{ formatCurrency(pedido.frete) }}</dd></div>
          <div v-if="pedido.desconto" class="flex justify-between py-0.5"><dt>Desconto</dt><dd class="tabular-nums">− {{ formatCurrency(pedido.desconto) }}</dd></div>
          <div class="flex justify-between border-t border-neutral-800 mt-1 pt-1 font-black text-sm">
            <dt>Total</dt><dd class="tabular-nums">{{ formatCurrency(pedido.valor_total ?? 0) }}</dd>
          </div>
        </dl>
      </div>

      <div v-if="comPreco && pedido.parcelas.length > 1" class="mt-3 text-xs">
        <p class="text-[10px] font-bold uppercase tracking-widest text-neutral-500 mb-1">Parcelas combinadas</p>
        <p>
          <span v-for="(p, i) in pedido.parcelas" :key="p.numero">
            {{ p.numero }}ª em {{ p.dias }} dias: {{ formatCurrency(p.valor ?? 0) }}<template v-if="i < pedido.parcelas.length - 1"> · </template>
          </span>
        </p>
      </div>

      <div v-if="pedido.observacao" class="mt-3 border border-neutral-300 rounded-lg px-3 py-2 text-xs">
        <strong>Observação:</strong> {{ pedido.observacao }}
      </div>

      <div class="mt-12 grid grid-cols-2 gap-10 text-[10px] text-neutral-600 text-center">
        <div class="border-t border-neutral-500 pt-1">Comprador</div>
        <div class="border-t border-neutral-500 pt-1">Fornecedor — de acordo</div>
      </div>

      <PrintFooter />
    </div>
  </Teleport>
</template>

<style>
/* Escopado em `.pedido-compra-folha`: o print-a4.css é global e serve às vias
   de OS e de venda em produção — não se mexe nele por causa de uma folha nova. */
@media print {
  .pedido-compra-folha .tabela-itens thead {
    display: table-header-group;
  }
  .pedido-compra-folha header {
    page-break-inside: avoid;
  }
}
</style>
