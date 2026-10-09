<script setup lang="ts">
/**
 * @component FaltasPrint
 * @description As faltas da OS em A4, para levar ao telefone (Spec 10B D18).
 * Sai pelo mesmo caminho de impressão das outras vias (cabeçalho da empresa).
 *
 * Preto e branco (o `check:print-bw` barra cor) e NENHUM preço (D9).
 */
import PrintCompanyHeader from '@/shared/components/print/a4/PrintCompanyHeader.vue';
import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';

import type { FaltasDaOS } from '../schemas/separacao.schema';
import { quantidadeComUnidade } from '../utils/quantidades';

defineProps<{ faltas: FaltasDaOS }>();

const { companyInfo } = useCompanyPrintInfo();
/** A hora em que a folha foi impressa (a do computador da loja). */
const emitidaEm = new Date().toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
</script>

<template>
  <!-- Teleport: o print-a4.css esconde tudo o que não for filho direto do body. -->
  <Teleport to="body">
    <div class="print-container faltas-os hidden print:block bg-white text-black font-sans leading-snug" data-testid="faltas-print">
      <PrintCompanyHeader
        :company="companyInfo"
        document-label="FALTAS DE MATERIAL"
        :document-number="faltas.numero_os"
        date-label="Emitida em"
        :date-value="emitidaEm"
      />

      <p v-if="faltas.cliente" class="mt-3 text-sm">Cliente: <strong>{{ faltas.cliente }}</strong></p>

      <table class="mt-4 w-full border-collapse text-sm">
        <thead>
          <tr class="border-b-2 border-black text-left">
            <th class="py-1 pr-2">Produto</th>
            <th class="py-1 pr-2 text-right">Faltam</th>
            <th class="py-1 pr-2">Localização</th>
            <th class="py-1">Fornecedor</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in faltas.itens" :key="item.produto_id" class="border-b border-neutral-300">
            <td class="py-1 pr-2">{{ item.descricao }}</td>
            <td class="py-1 pr-2 text-right tabular-nums font-bold">{{ quantidadeComUnidade(item.faltam_milesimos, item.unidade) }}</td>
            <td class="py-1 pr-2">{{ item.localizacao || '—' }}</td>
            <td class="py-1">
              <template v-if="item.fornecedor">
                {{ item.fornecedor.nome }}<template v-if="item.fornecedor.telefone"> · {{ item.fornecedor.telefone }}</template>
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!faltas.itens.length" class="mt-4 text-sm">Nada a comprar: o estoque cobre esta OS.</p>

      <PrintFooter />
    </div>
  </Teleport>
</template>
