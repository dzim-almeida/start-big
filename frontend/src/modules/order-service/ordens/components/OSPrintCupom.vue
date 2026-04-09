<script setup lang="ts">
import { computed } from 'vue';

import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import { formatCurrency } from '@/shared/utils/finance';
import { formatCNPJ, formatCPF } from '@/shared/utils/document.utils';
import { useDateFormat } from '@vueuse/core';
import { useAuthStore } from '@/shared/stores/auth.store';
import { getClienteNome, getPaymentDisplayName } from '../../shared/utils/formatters';

interface PrintCupomProps {
  orderService: OrderServiceReadDataType | null;
  type: 'ENTRADA' | 'SAIDA' | 'CANCELAMENTO';
}

const props = defineProps<PrintCupomProps>();

const authStore = useAuthStore();

const SEPARATOR = '────────────────────────────';

const companyInfo = computed(() => {
  const company = authStore.userData?.empresa;
  const address = company?.enderecos[0];

  const addressString: string[] = [];
  if (address?.logradouro) addressString.push(address.logradouro);
  if (address?.numero) addressString.push(address.numero);
  if (address?.bairro) addressString.push(address.bairro);

  const addressRow1 = addressString.join(', ');
  const addressRow2 =
    address?.cidade && address?.estado ? `${address.cidade} - ${address.estado}` : '';

  return {
    name: company?.nome_fantasia ? company.nome_fantasia : company?.razao_social || 'StartBig ERP',
    cnpj: formatCNPJ(company!.documento),
    addressRow1: addressRow1 || 'Endereço não informado',
    addressRow2: addressRow1 ? addressRow2 : '',
    contact: company?.celular || company?.telefone || 'Contato não informado',
  };
});

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

  return useDateFormat(dateStr, 'DD/MM/YYYY HH:mm').value;
});

const clienteDoc = computed(() => {
  const cliente = props.orderService?.cliente as { cpf?: string; cnpj?: string } | undefined;
  if (!cliente) return '';
  if (cliente.cpf) return formatCPF(cliente.cpf);
  if (cliente.cnpj) return formatCNPJ(cliente.cnpj);
  return '';
});

const clientePhone = computed(() => {
  const cliente = props.orderService?.cliente as { celular?: string; telefone?: string } | undefined;
  return cliente?.celular || cliente?.telefone || '';
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
    <!-- ═══ CABEÇALHO EMPRESA ═══ -->
    <div class="text-center mb-1">
      <div class="font-bold text-sm uppercase">{{ companyInfo.name }}</div>
      <div>{{ companyInfo.cnpj }}</div>
      <div>{{ companyInfo.addressRow1 }}</div>
      <div v-if="companyInfo.addressRow2">{{ companyInfo.addressRow2 }}</div>
      <div>TEL: {{ companyInfo.contact }}</div>
    </div>

    <div class="separator">{{ SEPARATOR }}</div>

    <!-- ═══ TÍTULO + OS + DATA ═══ -->
    <div class="text-center font-bold my-1">{{ title }}</div>
    <div class="separator">{{ SEPARATOR }}</div>

    <div class="flex justify-between my-1">
      <span>OS: <strong>{{ orderService.numero_os }}</strong></span>
    </div>
    <div>Data: {{ date }}</div>

    <div class="separator">{{ SEPARATOR }}</div>

    <!-- ═══ DADOS DO CLIENTE ═══ -->
    <div class="section">
      <div class="font-bold mb-0.5">CLIENTE</div>
      <div>{{ getClienteNome(orderService.cliente) }}</div>
      <div v-if="clienteDoc">Doc: {{ clienteDoc }}</div>
      <div v-if="clientePhone">Tel: {{ clientePhone }}</div>
    </div>

    <div class="separator">{{ SEPARATOR }}</div>

    <!-- ═══ DADOS DO EQUIPAMENTO ═══ -->
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

    <!-- ═══ DEFEITO RELATADO ═══ -->
    <div class="section">
      <div class="font-bold mb-0.5">DEFEITO RELATADO</div>
      <div>{{ orderService.defeito_relatado }}</div>
    </div>

    <!-- ═══ OBSERVAÇÕES ═══ -->
    <template v-if="orderService.observacoes">
      <div class="separator">{{ SEPARATOR }}</div>
      <div class="section">
        <div class="font-bold mb-0.5">OBSERVACOES</div>
        <div class="whitespace-pre-line">{{ orderService.observacoes }}</div>
      </div>
    </template>

    <!-- ═══════════════════════════════════════ -->
    <!-- CONTEÚDO CONDICIONAL POR TIPO          -->
    <!-- ═══════════════════════════════════════ -->

    <!-- ──── SAÍDA: Diagnóstico + Solução ──── -->
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

      <!-- ──── SAÍDA: Itens ──── -->
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

      <!-- ──── SAÍDA: Pagamentos ──── -->
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

      <!-- ──── SAÍDA: Totais ──── -->
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
        <div class="flex justify-between font-bold text-sm mt-1">
          <span>TOTAL:</span>
          <span>{{ formatCurrency(paymentTotal) }}</span>
        </div>
      </div>
    </template>

    <!-- ──── CANCELAMENTO ──── -->
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

    <!-- ──── ENTRADA: Condições ──── -->
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

    <!-- ═══ ASSINATURAS ═══ -->
    <div class="separator mt-4">{{ SEPARATOR }}</div>
    <div class="section mt-3">
      <div class="signature-line"></div>
      <div class="text-center font-bold">Tecnico Responsavel</div>
    </div>
    <div class="section mt-4">
      <div class="signature-line"></div>
      <div class="text-center font-bold">Assinatura do Cliente</div>
      <div class="text-center" v-if="orderService.cliente">
        {{ getClienteNome(orderService.cliente) }}
      </div>
    </div>

    <!-- ═══ RODAPÉ ═══ -->
    <div class="separator mt-2">{{ SEPARATOR }}</div>
    <div class="text-center mt-1 mb-2">
      <div>{{ new Date().toLocaleString('pt-BR') }}</div>
      <div class="font-bold">SISTEMA STARTBIG</div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  @page {
    margin: 0;
    size: 80mm auto;
  }

  body {
    visibility: hidden;
    background: white;
  }

  .print-cupom-container {
    visibility: visible;
    position: absolute;
    left: 0;
    top: 0;
    width: 80mm;
    margin: 0;
    padding: 4mm;
    display: block !important;
    background: white;
    font-family: 'Courier New', Courier, monospace;
    font-size: 11px;
    color: black;
    line-height: 1.3;
  }

  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .print-cupom-container table,
  .print-cupom-container .section {
    page-break-inside: avoid;
  }
}

.separator {
  text-align: center;
  letter-spacing: -1px;
  color: black;
}

.section {
  margin: 4px 0;
}

.item-row {
  margin-bottom: 4px;
  padding-bottom: 2px;
  border-bottom: 1px dotted black;
}

.item-row:last-child {
  border-bottom: none;
}

.signature-line {
  border-top: 1px solid black;
  width: 80%;
  margin: 0 auto 4px;
}

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.text-center {
  text-align: center;
}

.text-justify {
  text-align: justify;
}

.font-bold {
  font-weight: bold;
}

.text-sm {
  font-size: 12px;
}

.whitespace-pre-line {
  white-space: pre-line;
}

.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.mb-0\.5 { margin-bottom: 2px; }
.mb-1 { margin-bottom: 4px; }
.mb-2 { margin-bottom: 8px; }
.my-1 { margin-top: 4px; margin-bottom: 4px; }
</style>
