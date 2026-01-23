<script setup lang="ts">
/**
 * ===========================================================================
 * COMPONENTE: BasePagination
 * DESCRICAO: Footer padrao de tabelas com total de itens e paginacao
 * ===========================================================================
 *
 * USO:
 * <BasePagination
 *   :current-page="currentPage"
 *   :total-pages="totalPages"
 *   :total-items="totalItems"
 *   item-label="cliente"
 *   @update:current-page="setPage"
 * />
 * ===========================================================================
 */

import { ChevronLeft, ChevronRight } from 'lucide-vue-next';

interface Props {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  /** Label do item no singular (ex: "cliente", "orçamento", "OS") */
  itemLabel?: string;
  /** Label do item no plural (ex: "clientes", "orçamentos", "OS") - se não informado, adiciona 's' ao singular */
  itemLabelPlural?: string;
}

const props = withDefaults(defineProps<Props>(), {
  itemLabel: 'registro',
  itemLabelPlural: '',
});

const emit = defineEmits<{
  'update:currentPage': [page: number];
}>();

// ===========================================================================
// COMPUTED
// ===========================================================================

function getItemLabel(): string {
  if (props.totalItems === 1) {
    return props.itemLabel;
  }
  return props.itemLabelPlural || `${props.itemLabel}s`;
}

// ===========================================================================
// HANDLERS
// ===========================================================================

function prevPage() {
  if (props.currentPage > 1) {
    emit('update:currentPage', props.currentPage - 1);
  }
}

function nextPage() {
  if (props.currentPage < props.totalPages) {
    emit('update:currentPage', props.currentPage + 1);
  }
}
</script>

<template>
  <div class="px-4 py-3 border-t border-slate-100 bg-slate-50/30 flex items-center justify-between">
    <!-- Total de Itens (Esquerda) -->
    <span class="text-xs font-medium text-slate-500">
      {{ totalItems }} {{ getItemLabel() }} cadastrado{{ totalItems !== 1 ? 's' : '' }}
    </span>

    <!-- Paginação (Direita) - sempre visível se tiver itens -->
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="p-2 rounded-lg hover:bg-slate-100 text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        :disabled="currentPage <= 1"
        @click="prevPage"
      >
        <ChevronLeft :size="18" />
      </button>
      <span class="text-xs font-medium text-slate-700 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
        Página {{ currentPage }} de {{ totalPages }}
      </span>
      <button
        type="button"
        class="p-2 rounded-lg hover:bg-slate-100 text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        :disabled="currentPage >= totalPages"
        @click="nextPage"
      >
        <ChevronRight :size="18" />
      </button>
    </div>
  </div>
</template>
