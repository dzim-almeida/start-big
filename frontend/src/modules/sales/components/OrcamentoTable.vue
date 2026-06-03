<script setup lang="ts">
import { Pencil, Trash2, ArrowRightLeft, Eye, Printer } from 'lucide-vue-next';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useOrcamentoTable } from '../composables/flows/useOrcamentoTable';
import { useOrcamentoModal } from '../composables/flows/useOrcamentoModal';

import { ORCAMENTO_FILTER_CONFIG } from '../constants';

const { searchTerm, activeFilter, goToPage, orcamentos, isLoading } = useOrcamentoTable();
const { openOrcamentoModal } = useOrcamentoModal();

const emit = defineEmits<{
  (e: 'delete', orcamentoId: number): void;
  (e: 'converter', orcamentoId: number): void;
  (e: 'print', orcamentoId: number): void;
}>();
</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-empty="orcamentos?.orcamentos.length === 0"
    :current-page="orcamentos?.page"
    :total-pages="orcamentos?.total_pages"
    :total-items="orcamentos?.total"
    item-label="Orçamento"
    item-label-plural="Orçamentos"
    empty-title="Nenhum orçamento encontrado"
    empty-description='Clique em "Novo Orçamento" para criar um orçamento'
    @update:current-page="goToPage"
  >
    <template #toolbar>
      <BaseSearchInput v-model="searchTerm" placeholder="Buscar por número, funcionário..." class="min-w-64 flex-1" />
      <BaseFilter v-model="activeFilter" :filter-config="ORCAMENTO_FILTER_CONFIG" button-label="Filtros" />
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-120">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">Nº Orçamento</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Funcionário</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Data</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Valor</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-32">Ações Rápidas</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="orc in orcamentos?.orcamentos"
            :key="orc.id"
            class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
            @click="openOrcamentoModal(orc.id)"
          >
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div
                class="w-10 h-10 bg-brand-primary/10 rounded-xl flex flex-col items-center justify-center text-brand-primary"
              >
                <span class="text-[7px] opacity-70 font-medium leading-none">ORC</span>
                <span class="text-sm font-bold leading-none mt-0.5">{{ orc.id }}</span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span class="text-sm font-semibold text-zinc-900">
                {{ orc.funcionario?.nome ?? '—' }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center gap-2">
                <span
                  :class="[
                    'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                    orc.convertido ? 'bg-green-50 text-green-700' : 'bg-blue-50 text-blue-700',
                  ]"
                >
                  {{ orc.convertido ? 'Convertido' : 'Ativo' }}
                </span>
                <span
                  v-if="orc.convertido && orc.venda_id"
                  class="px-2 py-0.5 rounded-full text-[10px] font-semibold text-brand-primary bg-brand-primary/10"
                >
                  Venda #{{ String(orc.venda_id).padStart(6, '0') }}
                </span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600">
              {{ orc.atualizado_em }}
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600">
              <span v-if="orc.total > 0">{{ formatCurrency(orc.total) }}</span>
              <span v-else class="text-zinc-300">—</span>
            </td>

            <!-- Quick Actions -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <!-- Ativo: editar, imprimir, converter, excluir -->
                <template v-if="!orc.convertido">
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-blue-50 hover:text-brand-primary"
                    title="Editar"
                    @click.stop="openOrcamentoModal(orc.id)"
                  >
                    <Pencil class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
                    title="Imprimir"
                    @click.stop="emit('print', orc.id)"
                  >
                    <Printer class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-green-50 hover:text-green-600"
                    title="Converter em Venda"
                    @click.stop="emit('converter', orc.id)"
                  >
                    <ArrowRightLeft class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-red-50 hover:text-red-600"
                    title="Excluir"
                    @click.stop="emit('delete', orc.id)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </template>

                <!-- Convertido: visualizar, imprimir -->
                <template v-else>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-blue-50 hover:text-brand-primary"
                    title="Visualizar"
                    @click.stop="openOrcamentoModal(orc.id)"
                  >
                    <Eye class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
                    title="Imprimir"
                    @click.stop="emit('print', orc.id)"
                  >
                    <Printer class="h-4 w-4" />
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
