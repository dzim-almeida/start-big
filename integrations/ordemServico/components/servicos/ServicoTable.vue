<!--
===========================================================================
ARQUIVO: ServicoTable.vue
MODULO: Ordem de Servico
DESCRICAO: Tabela de listagem de servicos do catalogo. Inclui busca,
           filtro por status e acoes de edicao/toggle de status.
===========================================================================

PROPS:
- servicos: Lista de servicos para exibicao
- isLoading: Estado de carregamento
- searchQuery: Texto atual de busca
- activeFilterStatus: Filtro de status ativo (todos/ativos/inativos)
- currentPage, totalPages: Controle de paginacao

EMITS:
- edit: Abre modal de edicao do servico
- toggleStatus: Abre modal de confirmacao para ativar/desativar
- search: Texto de busca alterado
- filterChange: Filtro de status alterado
- pageChange: Pagina alterada

COLUNAS:
- Descricao: Nome/descricao do servico
- Valor: Preco base formatado em R$
- Status: Badge Ativo/Inativo
- Acoes: Editar (Pencil) | Toggle (Power)

LAYOUT:
- Toolbar: Campo de busca + Dropdown de filtro
- Tabela com colunas fixas
- Paginacao via BaseTableContainer
===========================================================================
-->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { Pencil, Power, Search, Filter } from 'lucide-vue-next';
import type { ServicoRead } from '../../types/servicos.types';
import { formatCurrency } from '@/shared/utils/finance';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';

interface Props {
  servicos: ServicoRead[];
  isLoading?: boolean;
  searchQuery?: string;
  activeFilterStatus?: string;
  currentPage?: number;
  totalPages?: number;
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  searchQuery: '',
  activeFilterStatus: 'todos',
  currentPage: 1,
  totalPages: 1,
});

const emit = defineEmits<{
  edit: [servico: ServicoRead];
  toggleStatus: [servico: ServicoRead];
  search: [value: string];
  filterChange: [value: string];
  pageChange: [page: number];
}>();

const statusOptions = [
  { value: 'todos', label: 'Todos' },
  { value: 'ativos', label: 'Ativos' },
  { value: 'inativos', label: 'Inativos' },
];

const statusConfig = {
  true: {
    label: 'Ativo',
    class: 'bg-emerald-50 text-emerald-600',
  },
  false: {
    label: 'Inativo',
    class: 'bg-red-50 text-red-600',
  },
};

function handleEdit(servico: ServicoRead) {
  emit('edit', servico);
}

function handleToggleStatus(servico: ServicoRead) {
  emit('toggleStatus', servico);
}

function handleSearch(event: Event) {
  const target = event.target as HTMLInputElement;
  emit('search', target.value);
}

// Filter Logic
const isFilterOpen = ref(false);
const filterContainerRef = ref<HTMLDivElement | null>(null);

function toggleFilter() {
    isFilterOpen.value = !isFilterOpen.value;
}

function handleClickOutside(event: MouseEvent) {
    if (filterContainerRef.value && !filterContainerRef.value.contains(event.target as Node)) {
        isFilterOpen.value = false;
    }
}

const activeFilterLabel = computed(() => {
    if (props.activeFilterStatus === 'todos') return 'Todos';
    const option = statusOptions.find(o => o.value === props.activeFilterStatus);
    return option ? option.label : props.activeFilterStatus;
});

onMounted(() => {
    document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('mousedown', handleClickOutside);
});

function handleFilterChange(value: string | undefined) {
  emit('filterChange', value || 'todos');
  isFilterOpen.value = false;
}
</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-empty="servicos.length === 0"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="servicos.length"
    item-label="serviço"
    empty-title="Nenhum serviço encontrado"
    @update:current-page="$emit('pageChange', $event)"
  >
    <!-- Toolbar -->
    <template #toolbar>
        <div class="flex flex-1 w-full gap-4">
            <div class="relative flex-1 max-w-md">
               <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                 <Search :size="18" class="text-zinc-400" />
               </div>
               <input
                 type="text"
                 :value="searchQuery"
                 placeholder="Buscar por descrição..."
                 class="w-full pl-11 pr-4 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary transition-all placeholder:text-zinc-400"
                 @input="handleSearch"
               />
            </div>
            
            <div class="w-auto">
               <div class="relative" ref="filterContainerRef">
                 <button 
                    @click="toggleFilter"
                    class="px-3 py-2.5 rounded-xl border bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300 transition-all flex items-center justify-between gap-2 relative min-w-30"
                    title="Filtrar por status"
                 >
                    <div class="flex items-center gap-2 w-full justify-between">
                        <span class="text-sm font-medium">{{ activeFilterLabel }}</span>
                        <Filter :size="16" class="text-zinc-400" />
                    </div>
                 </button>

                 <!-- Dropdown -->
                 <div 
                    v-if="isFilterOpen"
                    class="absolute right-0 top-full mt-2 w-48 bg-white border border-zinc-100 rounded-xl shadow-xl z-50 py-2 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 origin-top-right ring-1 ring-zinc-200"
                 >
                    <div class="px-4 py-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">
                        Filtrar Status
                    </div>
                    
                    <div class="h-px bg-zinc-100 mx-0 mb-1"></div>

                    <button
                        v-for="opt in statusOptions"
                        :key="opt.value"
                        @click="handleFilterChange(opt.value)"
                        class="w-full px-4 py-2.5 text-sm text-left flex items-center justify-between hover:bg-zinc-50 transition-colors group"
                        :class="activeFilterStatus === opt.value ? 'text-brand-primary font-medium' : 'text-zinc-600 font-medium'"
                    >
                        <span>{{ opt.label }}</span>
                        <!-- Dot indicator for active -->
                        <div 
                            v-if="activeFilterStatus === opt.value" 
                            class="w-2 h-2 rounded-full bg-brand-primary"
                        ></div>
                    </button>
                 </div>
               </div>
            </div>
        </div>
    </template>

    <!-- Table -->
    <table class="w-full text-left">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">DESCRIÇÃO</th>
            <th class="px-4 md:px-6 py-3 md:py-4">VALOR</th>
            <th class="px-4 md:px-6 py-3 md:py-4">STATUS</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right">AÇÕES</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="servico in servicos"
            :key="servico.id"
            class="hover:bg-zinc-50/50 transition-colors group"
          >
            <td class="px-4 md:px-6 py-3 md:py-4">
              <span class="text-sm font-medium text-zinc-900">
                {{ servico.descricao }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span class="text-sm font-semibold text-brand-primary">
                {{ formatCurrency(servico.valor) }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  statusConfig[String(servico.ativo) as 'true' | 'false'].class,
                ]"
              >
                {{ statusConfig[String(servico.ativo) as 'true' | 'false'].label }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end gap-2">
                <button
                  type="button"
                  class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors"
                  title="Editar servico"
                  @click="handleEdit(servico)"
                >
                  <Pencil :size="16" />
                </button>

                <button
                  type="button"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    servico.ativo
                      ? 'text-zinc-400 hover:text-red-500 hover:bg-red-50'
                      : 'text-zinc-400 hover:text-emerald-500 hover:bg-emerald-50',
                  ]"
                  :title="servico.ativo ? 'Desativar servico' : 'Ativar servico'"
                  @click="handleToggleStatus(servico)"
                >
                  <Power :size="16" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
  </BaseTableContainer>
</template>
