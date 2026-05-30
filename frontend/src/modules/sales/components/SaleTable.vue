<script setup lang="ts">
import { Pencil, Eye, CheckCircle, XCircle, RotateCcw, Printer } from 'lucide-vue-next';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useSaleTable } from '../composables/flows/useSaleTable';
import { useSaleModal } from '../composables/flows/useSaleModal';

import { SALE_FILTERS, STATUS_COLORS, SALE_FILTER_CHIPS } from '../constants';

const { searchTerm, activeFilter, goToPage, sales, isLoading } = useSaleTable();
const { openSaleViewModal, openSaleEditModal } = useSaleModal();

const emit = defineEmits<{
  (e: 'cancel', saleId: number): void;
  (e: 'finish', saleId: number): void;
  (e: 'reopen', saleId: number): void;
  (e: 'print', saleId: number, status: string): void;
}>();
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
      <BaseSearchInput v-model="searchTerm" placeholder="Buscar por número, cliente..." class="min-w-64 flex-1" />
      <div class="flex items-center gap-2 shrink-0">
        <button
          v-for="(config, key) in SALE_FILTER_CHIPS"
          :key="key"
          type="button"
          @click="activeFilter = activeFilter === key ? null : (key as typeof activeFilter)"
          :class="[
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer select-none',
            activeFilter === key
              ? config.activeClass
              : 'border-zinc-200 text-zinc-500 hover:border-zinc-300 hover:text-zinc-700'
          ]"
        >
          <span :class="['inline-block w-2 h-2 rounded-full shrink-0', config.dotColor]" />
          {{ config.label }}
        </button>
      </div>
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-160">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">Nº Orçamento</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Nº Venda</th>
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
            @click="sale.status !== 'ORCAMENTO' ? openSaleViewModal(sale.id) : openSaleEditModal(sale.id)"
          >
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div
                class="w-10 h-10 bg-brand-primary/10 rounded-xl flex flex-col items-center justify-center text-brand-primary"
              >
                <span class="text-[7px] opacity-70 font-medium leading-none">ORC</span>
                <span class="text-sm font-bold leading-none mt-0.5">{{ sale.id }}</span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div
                v-if="sale.numero_venda"
                class="w-10 h-10 bg-green-50 rounded-xl flex flex-col items-center justify-center text-green-700"
              >
                <span class="text-[7px] opacity-70 font-medium leading-none">VENDA</span>
                <span class="text-sm font-bold leading-none mt-0.5">{{ sale.numero_venda }}</span>
              </div>
              <span v-else class="text-zinc-300">—</span>
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

            <!-- Quick Actions -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <!-- ORCAMENTO actions -->
                <template v-if="sale.status === 'ORCAMENTO'">
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-blue-50 hover:text-brand-primary"
                    title="Editar"
                    @click.stop="openSaleEditModal(sale.id)"
                  >
                    <Pencil class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
                    title="Imprimir Orçamento"
                    @click.stop="emit('print', sale.id, sale.status)"
                  >
                    <Printer class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-green-50 hover:text-green-600"
                    title="Finalizar"
                    @click.stop="emit('finish', sale.id)"
                  >
                    <CheckCircle class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-red-50 hover:text-red-600"
                    title="Cancelar"
                    @click.stop="emit('cancel', sale.id)"
                  >
                    <XCircle class="h-4 w-4" />
                  </button>
                </template>

                <!-- FINALIZADA actions -->
                <template v-else-if="sale.status === 'FINALIZADA'">
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-blue-50 hover:text-brand-primary"
                    title="Visualizar"
                    @click.stop="openSaleViewModal(sale.id)"
                  >
                    <Eye class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
                    title="Imprimir"
                    @click.stop="emit('print', sale.id, sale.status)"
                  >
                    <Printer class="h-4 w-4" />
                  </button>
                </template>

                <!-- CANCELADA actions -->
                <template v-else-if="sale.status === 'CANCELADA'">
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-blue-50 hover:text-brand-primary"
                    title="Visualizar"
                    @click.stop="openSaleViewModal(sale.id)"
                  >
                    <Eye class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-amber-50 hover:text-amber-600"
                    title="Reabrir"
                    @click.stop="emit('reopen', sale.id)"
                  >
                    <RotateCcw class="h-4 w-4" />
                  </button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </BaseTableContainer>
</template>
