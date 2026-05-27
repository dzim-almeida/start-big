<script setup lang="ts">
import { computed } from 'vue';
import { User, CreditCard, ShoppingBag } from 'lucide-vue-next';
import type { SaleRead } from '../../schemas/sale.schema';
import { formatCurrency } from '@/shared/utils/finance';
import {
  useCompanyPrintInfo,
  getClienteNome,
  getClienteDoc,
  getClientePhone,
  formatPrintDate,
  formatPrintPhone,
  formatPrintDoc,
} from '@/shared/utils/print.utils';

import PrintCompanyHeader from '@/shared/components/print/a4/PrintCompanyHeader.vue';
import PrintSignatures from '@/shared/components/print/a4/PrintSignatures.vue';
import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';

const props = defineProps<{
  sale: SaleRead | null;
  type: 'ORCAMENTO' | 'VENDA';
  paymentMethodResolver: (id: number) => string;
}>();

const { companyInfo } = useCompanyPrintInfo();

const title = computed(() => {
  return props.type === 'ORCAMENTO' ? 'ORÇAMENTO' : 'COMPROVANTE DE VENDA';
});

const documentLabel = computed(() => {
  return props.type === 'VENDA' ? 'Nº da Venda' : 'Nº do Orçamento';
});

const documentNumber = computed(() => {
  if (props.type === 'VENDA' && props.sale?.numero_venda) {
    return String(props.sale.numero_venda).padStart(6, '0');
  }
  return String(props.sale?.id ?? 0).padStart(6, '0');
});

const totalPago = computed(() => {
  if (!props.sale?.pagamentos) return 0;
  return props.sale.pagamentos.reduce((acc, pg) => acc + pg.valor, 0);
});
</script>

<template>
  <div v-if="sale" class="print-container hidden print:block bg-white text-black font-sans leading-tight">
    <PrintCompanyHeader
      :company="companyInfo"
      :document-label="documentLabel"
      :document-number="documentNumber"
      date-label="Data"
      :date-value="formatPrintDate(sale.criado_em)"
    />

    <!-- Subinfo: Orçamento ref quando é VENDA -->
    <div v-if="type === 'VENDA'" class="text-right -mt-3 mb-3 pr-1">
      <span class="text-[10px] text-slate-500">Orçamento Nº {{ String(sale.id).padStart(6, '0') }}</span>
    </div>

    <div class="text-center py-2 mb-4 border-y-2 border-slate-200 bg-slate-50">
      <h2 class="text-lg font-black text-slate-800 uppercase tracking-widest">{{ title }}</h2>
    </div>

    <!-- Dados do Cliente -->
    <div class="mb-4">
      <div class="border border-slate-300 rounded-lg overflow-hidden">
        <div class="bg-slate-100 px-3 py-1.5 border-b border-slate-200 flex items-center gap-2">
          <User :size="14" class="text-slate-500" />
          <h3 class="text-xs font-bold uppercase text-slate-700">Dados do Cliente</h3>
        </div>
        <div class="p-3 text-xs space-y-1.5">
          <p><span class="font-bold text-slate-600">Nome:</span> {{ sale.cliente ? getClienteNome(sale.cliente as any) : 'Consumidor Final' }}</p>
          <div class="flex gap-4">
            <p v-if="getClienteDoc(sale.cliente as any)"><span class="font-bold text-slate-600">CPF/CNPJ:</span> {{ formatPrintDoc(getClienteDoc(sale.cliente as any)) }}</p>
            <p v-if="getClientePhone(sale.cliente as any)"><span class="font-bold text-slate-600">Telefone:</span> {{ formatPrintPhone(getClientePhone(sale.cliente as any)) }}</p>
          </div>
          <p v-if="sale.cliente?.id"><span class="font-bold text-slate-600">Cód. Cliente:</span> #{{ sale.cliente.id }}</p>
        </div>
      </div>
    </div>

    <!-- Tabela de Itens -->
    <div class="mb-4" v-if="sale.produtos?.length">
      <div class="flex items-center gap-2 mb-2">
        <ShoppingBag :size="14" class="text-slate-500" />
        <h3 class="text-xs font-bold uppercase text-slate-700">Itens da Venda</h3>
      </div>
      <table class="w-full text-xs text-left">
        <thead>
          <tr class="border-b-2 border-slate-800">
            <th class="py-2 pl-2 text-slate-600 uppercase font-bold w-[40%]">Produto</th>
            <th class="py-2 text-center text-slate-600 uppercase font-bold w-[12%]">SKU</th>
            <th class="py-2 text-center text-slate-600 uppercase font-bold w-[8%]">Qtd</th>
            <th class="py-2 text-right text-slate-600 uppercase font-bold w-[13%]">Unit.</th>
            <th class="py-2 text-right text-slate-600 uppercase font-bold w-[13%]">Desc.</th>
            <th class="py-2 pr-2 text-right text-slate-600 uppercase font-bold w-[14%]">Total</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200">
          <tr v-for="item in sale.produtos" :key="item.id">
            <td class="py-2 pl-2 text-slate-800">{{ item.nome }}</td>
            <td class="py-2 text-center text-slate-500">{{ item.sku || '-' }}</td>
            <td class="py-2 text-center text-slate-600">{{ item.quantidade }}</td>
            <td class="py-2 text-right text-slate-600">{{ formatCurrency(item.valor_unitario) }}</td>
            <td class="py-2 text-right text-red-600">{{ item.desconto > 0 ? `- ${formatCurrency(item.desconto)}` : '-' }}</td>
            <td class="py-2 pr-2 text-right font-bold text-slate-800">{{ formatCurrency(item.total) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagamentos (somente VENDA) -->
    <template v-if="type === 'VENDA'">
      <div class="grid grid-cols-2 gap-6 mb-4">
        <div>
          <p class="text-[10px] font-bold text-slate-500 uppercase mb-2 border-b border-slate-200 pb-1">Detalhes do Pagamento</p>
          <div v-if="sale.pagamentos?.length" class="space-y-1.5">
            <div v-for="pgto in sale.pagamentos" :key="pgto.id" class="flex justify-between items-center text-xs bg-slate-50 p-1.5 rounded border border-slate-100">
              <div class="flex items-center gap-2">
                <CreditCard :size="12" class="text-slate-400" />
                <span class="font-semibold text-slate-700">
                  {{ paymentMethodResolver(pgto.forma_pagamento_id) }}
                  <span v-if="pgto.parcelado && pgto.qtd_parcelas" class="text-[10px] text-slate-500 font-normal">({{ pgto.qtd_parcelas }}x)</span>
                </span>
              </div>
              <span class="font-bold text-slate-800">{{ formatCurrency(pgto.valor) }}</span>
            </div>
          </div>
          <div v-else class="text-xs text-slate-400 italic py-2">Nenhum pagamento registrado.</div>
        </div>

        <div class="space-y-1 text-right">
          <div class="flex justify-between text-xs text-slate-500">
            <span>Subtotal:</span>
            <span>{{ formatCurrency(sale.subtotal) }}</span>
          </div>
          <div v-if="sale.descontos > 0" class="flex justify-between text-xs text-red-600">
            <span>Desconto:</span>
            <span>- {{ formatCurrency(sale.descontos) }}</span>
          </div>
          <div v-if="sale.entrega > 0" class="flex justify-between text-xs text-green-600">
            <span>Entrega:</span>
            <span>+ {{ formatCurrency(sale.entrega) }}</span>
          </div>
          <div class="border-t border-slate-800 my-1 pt-1 flex justify-between items-end">
            <span class="text-sm font-bold text-slate-900 uppercase">Total:</span>
            <span class="text-xl font-black text-slate-900 leading-none">{{ formatCurrency(sale.total) }}</span>
          </div>
          <div class="flex justify-between text-xs text-slate-500">
            <span>Total Pago:</span>
            <span>{{ formatCurrency(totalPago) }}</span>
          </div>
          <div v-if="sale.troco > 0" class="flex justify-between text-xs text-amber-600">
            <span>Troco:</span>
            <span>{{ formatCurrency(sale.troco) }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Resumo financeiro (ORCAMENTO) -->
    <template v-else>
      <div class="mb-4">
        <div class="border border-slate-300 rounded-lg p-4">
          <p class="text-[10px] font-bold text-slate-500 uppercase mb-3 border-b border-slate-200 pb-1">Resumo Financeiro</p>
          <div class="space-y-1.5 text-xs">
            <div class="flex justify-between text-slate-500">
              <span>Subtotal:</span>
              <span>{{ formatCurrency(sale.subtotal) }}</span>
            </div>
            <div v-if="sale.descontos > 0" class="flex justify-between text-red-600">
              <span>Desconto:</span>
              <span>- {{ formatCurrency(sale.descontos) }}</span>
            </div>
            <div v-if="sale.entrega > 0" class="flex justify-between text-green-600">
              <span>Entrega:</span>
              <span>+ {{ formatCurrency(sale.entrega) }}</span>
            </div>
            <div class="border-t border-slate-800 my-1 pt-2 flex justify-between items-end">
              <span class="text-sm font-bold text-slate-900 uppercase">Total do Orçamento:</span>
              <span class="text-xl font-black text-slate-900 leading-none">{{ formatCurrency(sale.total) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Observações -->
    <div v-if="sale.observacao" class="mb-4 border border-dashed border-slate-300 rounded-lg p-3">
      <p class="text-[10px] font-bold text-slate-500 uppercase mb-1">Observações</p>
      <p class="text-xs text-slate-700 whitespace-pre-line">{{ sale.observacao }}</p>
    </div>

    <!-- Validade (ORCAMENTO) -->
    <div v-if="type === 'ORCAMENTO'" class="border border-brand-primary/20 bg-brand-primary-light/50 rounded-lg p-3 text-[10px] text-slate-700 text-justify leading-relaxed mb-6">
      <strong class="text-brand-primary uppercase">Validade:</strong>
      Este orçamento é válido por <strong>30 (trinta) dias</strong> a partir da data de emissão.
      Após este prazo, os valores e condições poderão ser alterados sem aviso prévio.
    </div>

    <PrintSignatures
      left-label="Vendedor"
      right-label="Assinatura do Cliente"
      :right-name="sale.cliente ? getClienteNome(sale.cliente as any) : undefined"
    />

    <PrintFooter />
  </div>
</template>

<style>
@import '@/shared/components/print/styles/print-a4.css';
</style>
