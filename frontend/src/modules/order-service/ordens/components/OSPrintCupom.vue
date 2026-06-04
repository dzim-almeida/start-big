<script setup lang="ts">
import { computed } from 'vue';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import { formatCurrency } from '@/shared/utils/finance';
import {
  useCompanyPrintInfo,
  getClienteNome,
  getClienteDoc,
  getClientePhone,
  getPaymentDisplayName,
  formatPrintDate,
  formatPrintDoc,
} from '@/shared/utils/print.utils';

import PrintCupomHeader from '@/shared/components/print/cupom/PrintCupomHeader.vue';
import PrintCupomSignatures from '@/shared/components/print/cupom/PrintCupomSignatures.vue';
import PrintCupomFooter from '@/shared/components/print/cupom/PrintCupomFooter.vue';

interface PrintCupomProps {
  orderService: OrderServiceReadDataType | null;
  type: 'ENTRADA' | 'SAIDA' | 'CANCELAMENTO';
}

const props = defineProps<PrintCupomProps>();

const { companyInfo } = useCompanyPrintInfo();

const SEPARATOR = '────────────────────────────';

const title = computed(() => {
  switch (props.type) {
    case 'ENTRADA':
      return 'COMPROVANTE DE ENTRADA';
    case 'SAIDA':
      return 'RECIBO E GARANTIA';
    case 'CANCELAMENTO':
      return 'CANCELAMENTO DE OS';
    default:
      return 'Cupom';
  }
});

const date = computed(() => {
  let dateStr: string;
  switch (props.type) {
    case 'ENTRADA':
      dateStr = props.orderService!.data_criacao;
      break;
    case 'SAIDA':
      dateStr = (props.orderService!.data_finalizacao as string) || props.orderService!.data_criacao;
      break;
    default:
      dateStr = props.orderService!.data_criacao;
  }
  return formatPrintDate(dateStr);
});

const clienteDoc = computed(() => {
  const doc = getClienteDoc(props.orderService?.cliente);
  return doc ? formatPrintDoc(doc) : '';
});

const clientePhone = computed(() => {
  return getClientePhone(props.orderService?.cliente);
});

const subTotal = computed(() => {
  if (!props.orderService) return 0;
  return props.orderService.itens.reduce((acc, item) => acc + item.valor_total, 0);
});

const paymentTotal = computed(() => {
  if (!props.orderService?.pagamentos) return 0;
  return props.orderService.pagamentos.reduce((acc, pay) => acc + pay.valor, 0);
});
</script>

<template>
  <div v-if="orderService" class="print-cupom-container hidden print:block">
    <PrintCupomHeader :company="companyInfo" />

    <div class="separator">{{ SEPARATOR }}</div>

    <div class="text-center font-bold my-1">{{ title }}</div>
    <div class="separator">{{ SEPARATOR }}</div>

    <div class="flex justify-between my-1">
      <span>OS: <strong>{{ orderService.numero_os }}</strong></span>
    </div>
    <div>Data: {{ date }}</div>

    <div class="separator">{{ SEPARATOR }}</div>

    <div class="section">
      <div class="font-bold mb-0.5">CLIENTE</div>
      <div>{{ getClienteNome(orderService.cliente) }}</div>
      <div v-if="clienteDoc">Doc: {{ clienteDoc }}</div>
      <div v-if="clientePhone">Tel: {{ clientePhone }}</div>
    </div>

    <div class="separator">{{ SEPARATOR }}</div>

    <div class="section">
      <div class="font-bold mb-0.5">EQUIPAMENTO</div>
      <div>{{ orderService.equipamento.tipo_equipamento }}</div>
      <div v-if="orderService.equipamento.marca">
        Marca: {{ orderService.equipamento.marca }}
      </div>
      <div v-if="orderService.equipamento.modelo">
        Modelo: {{ orderService.equipamento.modelo }}
      </div>
      <div v-if="orderService.equipamento.numero_serie">
        N/S: {{ orderService.equipamento.numero_serie }}
      </div>
      <div v-if="orderService.equipamento.cor">
        Cor: {{ orderService.equipamento.cor }}
      </div>
    </div>

    <div class="separator">{{ SEPARATOR }}</div>

    <div class="section">
      <div class="font-bold mb-0.5">DEFEITO RELATADO</div>
      <div>{{ orderService.defeito_relatado }}</div>
    </div>

    <template v-if="orderService.observacoes">
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section">
        <div class="font-bold mb-0.5">OBSERVACOES</div>
        <div class="whitespace-pre-line">{{ orderService.observacoes }}</div>
      </div>
    </template>

    <template v-if="type === 'SAIDA'">
      <template v-if="orderService.diagnostico || orderService.solucao">
        <div class="separator">{{ SEPARATOR }}</div>
        <div class="section">
          <div class="font-bold mb-0.5">LAUDO TECNICO</div>
          <div v-if="orderService.diagnostico">
            Diag: {{ orderService.diagnostico }}
          </div>
          <div v-if="orderService.solucao">
            Solucao: {{ orderService.solucao }}
          </div>
        </div>
      </template>

      <template v-if="orderService.itens?.length">
        <div class="separator">{{ SEPARATOR }}</div>
        <div class="section">
          <div class="font-bold mb-0.5">ITENS/SERVICOS</div>
          <div
            v-for="item in orderService.itens"
            :key="item.id"
            class="item-row"
          >
            <div>{{ item.nome }}</div>
            <div class="flex justify-between">
              <span>{{ item.quantidade }}x {{ formatCurrency(item.valor_unitario) }}</span>
              <span class="font-bold">{{ formatCurrency(item.valor_total) }}</span>
            </div>
          </div>
        </div>
      </template>

      <template v-if="orderService.pagamentos?.length">
        <div class="separator">{{ SEPARATOR }}</div>
        <div class="section">
          <div class="font-bold mb-0.5">PAGAMENTOS</div>
          <div
            v-for="pgto in orderService.pagamentos"
            :key="pgto.id"
            class="flex justify-between"
          >
            <span>
              {{ getPaymentDisplayName(pgto.forma_pagamento?.nome || 'Pagamento') }}
              <span v-if="pgto.parcelas > 1">({{ pgto.parcelas }}x)</span>
            </span>
            <span>{{ formatCurrency(pgto.valor) }}</span>
          </div>
        </div>
      </template>

      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section">
        <div class="flex justify-between">
          <span>Subtotal:</span>
          <span>{{ formatCurrency(subTotal) }}</span>
        </div>
        <div v-if="(orderService.desconto ?? 0) > 0" class="flex justify-between">
          <span>Desconto:</span>
          <span>-{{ formatCurrency(orderService.desconto ?? 0) }}</span>
        </div>
        <div v-if="(orderService.acrescimo ?? 0) > 0" class="flex justify-between">
          <span>Juros:</span>
          <span>+{{ formatCurrency(orderService.acrescimo ?? 0) }}</span>
        </div>
        <div class="flex justify-between font-bold text-sm mt-1">
          <span>TOTAL:</span>
          <span>{{ formatCurrency(paymentTotal) }}</span>
        </div>
        <template v-if="(orderService.acrescimo ?? 0) > 0">
          <div class="separator">{{ SEPARATOR }}</div>
          <div class="font-bold text-[9px] uppercase mb-0.5">Devolucao</div>
          <div class="flex justify-between text-[9px]">
            <span>Servico (dinheiro):</span>
            <span>{{ formatCurrency(paymentTotal - (orderService.acrescimo ?? 0)) }}</span>
          </div>
          <div class="flex justify-between text-[9px]">
            <span>Estorno cartao:</span>
            <span>{{ formatCurrency(paymentTotal) }}</span>
          </div>
        </template>
      </div>
    </template>

    <template v-else-if="type === 'CANCELAMENTO'">
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section">
        <div class="font-bold mb-0.5">MOTIVO DO CANCELAMENTO</div>
        <div>{{ (orderService as any).motivo_cancelamento || 'Motivo nao informado.' }}</div>
      </div>
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section text-justify">
        A OS acima foi cancelada nesta data.
        Equipamento devolvido ao cliente sem
        reparos ou com reparos parciais,
        isentando a assistencia de garantias
        sobre servicos nao concluidos.
      </div>
    </template>

    <template v-else>
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section text-justify">
        O cliente declara estar ciente que a
        empresa nao se responsabiliza por
        perda de dados nem por chips/cartoes
        deixados no aparelho. Autorizo a
        analise tecnica do equipamento.
      </div>
    </template>

    <PrintCupomSignatures
      left-label="Tecnico Responsavel"
      right-label="Assinatura do Cliente"
      :right-name="orderService.cliente ? getClienteNome(orderService.cliente) : undefined"
    />

    <PrintCupomFooter />
  </div>
</template>

<style>
@import '@/shared/components/print/styles/print-cupom.css';
</style>
