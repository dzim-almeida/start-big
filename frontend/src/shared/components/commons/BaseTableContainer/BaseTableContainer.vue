<script setup lang="ts">
/**
 * ===========================================================================
 * COMPONENTE: BaseTableContainer
 * DESCRICAO: Container padrao para tabelas do sistema com toolbar e paginacao
 * ===========================================================================
 *
 * SLOTS:
 * - toolbar: Conteudo da barra de ferramentas (busca, filtros)
 * - default: Conteudo da tabela
 * - empty: Estado vazio customizado
 * - loading: Estado de loading customizado
 *
 * USO:
 * <BaseTableContainer
 *   :is-loading="isLoading"
 *   :is-empty="items.length === 0"
 *   :current-page="currentPage"
 *   :total-pages="totalPages"
 *   :total-items="totalItems"
 *   item-label="cliente"
 *   empty-title="Nenhum cliente encontrado"
 *   empty-description="Clique em 'Novo Cliente' para cadastrar"
 *   @update:current-page="setPage"
 * >
 *   <template #toolbar>
 *     <SearchInput ... />
 *     <FilterDropdown ... />
 *   </template>
 *
 *   <table>...</table>
 * </BaseTableContainer>
 * ===========================================================================
 */

import { Search } from 'lucide-vue-next';
import BasePagination from '../BasePagination/BasePagination.vue';

interface Props {
  isLoading?: boolean;
  isEmpty?: boolean;
  // Paginação
  currentPage?: number;
  totalPages?: number;
  totalItems?: number;
  itemLabel?: string;
  itemLabelPlural?: string;
  // Empty State
  emptyTitle?: string;
  emptyDescription?: string;
}

withDefaults(defineProps<Props>(), {
  isLoading: false,
  isEmpty: false,
  currentPage: 1,
  totalPages: 1,
  totalItems: 0,
  itemLabel: 'registro',
  itemLabelPlural: '',
  emptyTitle: 'Nenhum registro encontrado',
  emptyDescription: '',
});

const emit = defineEmits<{
  'update:currentPage': [page: number];
}>();
</script>

<template>
  <div class="bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col h-full overflow-hidden">
    <!-- Toolbar -->
    <div
      v-if="$slots.toolbar"
      class="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-50/50"
    >
      <slot name="toolbar" />
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center py-12">
      <slot name="loading">
        <div class="flex flex-col items-center gap-3">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-primary"></div>
          <span class="text-sm text-slate-400">Carregando...</span>
        </div>
      </slot>
    </div>

    <!-- Empty State -->
    <div v-else-if="isEmpty" class="flex-1 flex items-center justify-center py-12">
      <slot name="empty">
        <div class="flex flex-col items-center gap-2 text-center px-4">
          <div class="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-2">
            <Search :size="24" class="text-slate-300" />
          </div>
          <span class="text-sm font-medium text-slate-500">{{ emptyTitle }}</span>
          <span v-if="emptyDescription" class="text-xs text-slate-400">{{ emptyDescription }}</span>
        </div>
      </slot>
    </div>

    <!-- Content -->
    <div v-else class="flex-1 overflow-auto">
      <slot />
    </div>

    <!-- Pagination Footer -->
    <BasePagination
      v-if="!isLoading && !isEmpty && totalItems > 0"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      :item-label="itemLabel"
      :item-label-plural="itemLabelPlural"
      @update:current-page="emit('update:currentPage', $event)"
    />
  </div>
</template>
