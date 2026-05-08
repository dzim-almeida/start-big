<script setup lang="ts">
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';

import { formatCurrency } from '@/shared/utils/finance';

import { useSaleTable } from '../composables/useSaleTable';
import { useSaleModal } from '../composables/useSaleModal';

import { SALE_FILTERS, STATUS_COLORS } from '../constants';

const { searchTerm, activeFilter, goToPage, sales, isLoading } = useSaleTable();
const { openSaleViewModal } = useSaleModal();

</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-empty="sales?.vendas.length === 0"
    :current-page="sales?.page"
    :total-pages="sales?.total_pages"
    :total-items="sales?.total"
    item-label="Venda"
    item-label-plural="Vendas"
    empty-title="Nenhuma venda encontrada"
    empty-description='Clique em "Nova Venda" para criar uma venda'
    @update:current-page="goToPage"
  >
    <template #toolbar>
      <BaseSearchInput v-model="searchTerm" placeholder="Buscar por número, cliente..." />
      <BaseFilter v-model="activeFilter" :filter-config="SALE_FILTERS" button-label="Filtros" />
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-160">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">Venda</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Cliente</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Data da Venda</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Valor</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-40">Ações Rápidas</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="sale in sales?.vendas"
            :key="sale.id"
            class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
            @click="openSaleViewModal(sale.id)"
          >
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div
                class="w-10 h-10 bg-brand-primary rounded-xl flex flex-col items-center justify-center text-white"
              >
                <span class="text-[7px] opacity-70 font-medium leading-none">VENDA</span>
                <span class="text-sm font-bold leading-none mt-0.5">{{ sale.id }}</span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex flex-col">
                <span class="text-sm font-semibold text-zinc-900 group-hover:text-brand-primary transition-colors">
                  <span v-if="!!sale.cliente">{{ sale.cliente?.tipo === "PF" ? sale.cliente?.nome : sale.cliente?.razao_social }}</span>
                  <span v-else class="text-red-400">Venda sem cliente</span>
                </span>
                <span class="text-[10px] text-zinc-400 mt-0.5">{{ sale.cliente?.tipo === "PF" ? sale.cliente?.cpf : sale.cliente?.cnpj }}</span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  STATUS_COLORS[sale.status]?.bg,
                  STATUS_COLORS[sale.status]?.text,
                ]"
              >
                {{ SALE_FILTERS[sale.status]?.label }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors">
              <span v-if="sale.status === 'FINALIZADA'">{{ sale.atualizado_em }}</span>
              <span v-else class="text-zinc-300">—</span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors">
              <span v-if="sale.total > 0">{{ formatCurrency(sale.total) }}</span>
              <span v-else class="text-zinc-300">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </BaseTableContainer>
</template>
