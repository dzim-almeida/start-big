<script setup lang="ts">
import { computed } from 'vue';
import type { SaleRead } from '../../schemas/sale.schema';
import { formatCurrency } from '@/shared/utils/finance';
import {
  useCompanyPrintInfo,
  getClienteNome,
  getClienteDoc,
  getClientePhone,
  formatPrintDate,
  formatPrintDoc,
} from '@/shared/utils/print.utils';

import PrintCupomHeader from '@/shared/components/print/cupom/PrintCupomHeader.vue';
import PrintCupomSignatures from '@/shared/components/print/cupom/PrintCupomSignatures.vue';
import PrintCupomFooter from '@/shared/components/print/cupom/PrintCupomFooter.vue';

const props = defineProps<{
  sale: SaleRead | null;
  type: 'ORCAMENTO' | 'VENDA';
  paymentMethodResolver: (id: number) => string;
}>();

const { companyInfo } = useCompanyPrintInfo();

const SEPARATOR = '────────────────────────────';

const title = computed(() => {
  return props.type === 'ORCAMENTO' ? 'ORCAMENTO' : 'COMPROVANTE DE VENDA';
});

const documentId = computed(() => {
  if (props.type === 'VENDA' && props.sale?.numero_venda) {
    return `VENDA: ${String(props.sale.numero_venda).padStart(6, '0')}`;
  }
  return `ORC: ${String(props.sale?.id ?? 0).padStart(6, '0')}`;
});

const clienteDoc = computed(() => {
  const doc = getClienteDoc(props.sale?.cliente as any);
  return doc ? formatPrintDoc(doc) : '';
});

const clientePhone = computed(() => {
  return getClientePhone(props.sale?.cliente as any);
});

const totalPago = computed(() => {
  if (!props.sale?.pagamentos) return 0;
  return props.sale.pagamentos.reduce((acc, pg) => acc + pg.valor, 0);
});
</script>

<template>
  <div v-if="sale" class="print-cupom-container hidden print:block">
    <PrintCupomHeader :company="companyInfo" />

    <div class="separator">{{ SEPARATOR }}</div>

    <div class="text-center font-bold my-1">{{ title }}</div>
    <div class="separator">{{ SEPARATOR }}</div>

    <div class="my-1">
      <div><strong>{{ documentId }}</strong></div>
      <div v-if="type === 'VENDA'">ORC: {{ String(sale.id).padStart(6, '0') }}</div>
      <div>Data: {{ formatPrintDate(sale.criado_em) }}</div>
    </div>

    <div class="separator">{{ SEPARATOR }}</div>

    <!-- Cliente -->
    <div class="section">
      <div class="font-bold mb-0.5">CLIENTE</div>
      <div>{{ getClienteNome(sale.cliente as any) }}</div>
      <div v-if="clienteDoc">Doc: {{ clienteDoc }}</div>
      <div v-if="clientePhone">Tel: {{ clientePhone }}</div>
    </div>

    <div class="separator">{{ SEPARATOR }}</div>

    <!-- Itens -->
    <div class="section" v-if="sale.produtos?.length">
      <div class="font-bold mb-0.5">ITENS</div>
      <div
        v-for="item in sale.produtos"
        :key="item.id"
        class="item-row"
      >
        <div>{{ item.nome }}</div>
        <div class="flex justify-between">
          <span>{{ item.quantidade }}x {{ formatCurrency(item.valor_unitario) }}</span>
          <span class="font-bold">{{ formatCurrency(item.total) }}</span>
        </div>
        <div v-if="item.desconto > 0" class="flex justify-between">
          <span>Desc:</span>
          <span>-{{ formatCurrency(item.desconto) }}</span>
        </div>
      </div>
    </div>

    <!-- Pagamentos (VENDA) -->
    <template v-if="type === 'VENDA' && sale.pagamentos?.length">
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section">
        <div class="font-bold mb-0.5">PAGAMENTOS</div>
        <div
          v-for="pgto in sale.pagamentos"
          :key="pgto.id"
          class="flex justify-between"
        >
          <span>
            {{ paymentMethodResolver(pgto.forma_pagamento_id) }}
            <span v-if="pgto.parcelado && pgto.qtd_parcelas">({{ pgto.qtd_parcelas }}x)</span>
          </span>
          <span>{{ formatCurrency(pgto.valor) }}</span>
        </div>
      </div>
    </template>

    <!-- Totais -->
    <div class="separator">{{ SEPARATOR }}</div>
    <div class="section">
      <div class="flex justify-between">
        <span>Subtotal:</span>
        <span>{{ formatCurrency(sale.subtotal) }}</span>
      </div>
      <div v-if="sale.descontos > 0" class="flex justify-between">
        <span>Desconto:</span>
        <span>-{{ formatCurrency(sale.descontos) }}</span>
      </div>
      <div v-if="sale.entrega > 0" class="flex justify-between">
        <span>Entrega:</span>
        <span>+{{ formatCurrency(sale.entrega) }}</span>
      </div>
      <div class="flex justify-between font-bold text-sm mt-1">
        <span>TOTAL:</span>
        <span>{{ formatCurrency(sale.total) }}</span>
      </div>
      <template v-if="type === 'VENDA'">
        <div class="flex justify-between">
          <span>Total Pago:</span>
          <span>{{ formatCurrency(totalPago) }}</span>
        </div>
        <div v-if="sale.troco > 0" class="flex justify-between">
          <span>Troco:</span>
          <span>{{ formatCurrency(sale.troco) }}</span>
        </div>
      </template>
    </div>

    <!-- Observações -->
    <template v-if="sale.observacao">
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section">
        <div class="font-bold mb-0.5">OBSERVACOES</div>
        <div class="whitespace-pre-line">{{ sale.observacao }}</div>
      </div>
    </template>

    <!-- Validade (ORCAMENTO) -->
    <template v-if="type === 'ORCAMENTO'">
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section text-justify">
        Orcamento valido por 30 dias a
        partir da data de emissao. Apos
        este prazo, valores e condicoes
        poderao ser alterados.
      </div>
    </template>

    <PrintCupomSignatures
      left-label="Vendedor"
      right-label="Assinatura do Cliente"
      :right-name="sale.cliente ? getClienteNome(sale.cliente as any) : undefined"
    />

    <PrintCupomFooter />
  </div>
</template>

<style>
@import '@/shared/components/print/styles/print-cupom.css';
</style>
