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

// No icon imports needed - using text buttons

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
  <div class="px-6 py-5 border-t border-zinc-100 bg-white rounded-b-2xl md:rounded-b-3xl flex flex-col md:flex-row items-center justify-between gap-4">
    <!-- Total de Itens (Esquerda) -->
    <span class="text-xs text-zinc-500 font-bold uppercase tracking-widest">
      {{ totalItems }} {{ getItemLabel() }}
    </span>

    <!-- Paginação (Direita) -->
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="h-9 px-4 rounded-lg text-xs font-bold transition-colors"
        :class="[
          currentPage <= 1
            ? 'text-zinc-400 bg-zinc-50 cursor-not-allowed'
            : 'text-zinc-700 bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 shadow-sm cursor-pointer'
        ]"
        :disabled="currentPage <= 1"
        @click="prevPage"
      >
        Anterior
      </button>
      <button
        class="h-9 w-9 rounded-lg bg-brand-primary text-white text-xs font-bold shadow-sm shadow-brand-primary/20 hover:bg-brand-primary/90 transition-all cursor-pointer"
      >
        {{ currentPage }}
      </button>
      <button
        type="button"
        class="h-9 px-4 rounded-lg text-xs font-bold transition-colors"
        :class="[
          currentPage >= totalPages
            ? 'text-zinc-400 bg-zinc-50 cursor-not-allowed'
            : 'text-zinc-700 bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 shadow-sm cursor-pointer'
        ]"
        :disabled="currentPage >= totalPages"
        @click="nextPage"
      >
        Proximo
      </button>
    </div>
  </div>
</template>
