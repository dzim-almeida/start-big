<script setup lang="ts">
import { computed } from 'vue';
import { ChevronLeft, ChevronRight } from 'lucide-vue-next';

interface Props {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemLabel?: string;
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

const itemLabel = computed(() => {
  if (props.totalItems === 1) return props.itemLabel;
  return props.itemLabelPlural || `${props.itemLabel}s`;
});

const hasPrev = computed(() => props.currentPage > 1);
const hasNext = computed(() => props.currentPage < props.totalPages);

const visiblePages = computed<(number | 'ellipsis')[]>(() => {
  const total = props.totalPages;
  const current = props.currentPage;

  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | 'ellipsis')[] = [1];

  if (current > 3) {
    pages.push('ellipsis');
  }

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push('ellipsis');
  }

  pages.push(total);

  return pages;
});

// ===========================================================================
// HANDLERS
// ===========================================================================

function goToPage(page: number) {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    emit('update:currentPage', page);
  }
}
</script>

<template>
  <div class="px-6 py-4 border-t border-zinc-100 bg-white rounded-b-2xl md:rounded-b-3xl flex flex-col md:flex-row items-center justify-between gap-3">
    <!-- Total de Itens -->
    <span class="text-xs text-zinc-400 font-medium tabular-nums">
      {{ totalItems }} {{ itemLabel }}
    </span>

    <!-- Controles de Paginação -->
    <div v-if="totalPages > 1" class="flex items-center gap-1">
      <!-- Anterior -->
      <button
        type="button"
        class="h-8 px-2.5 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
        :class="[
          hasPrev
            ? 'text-zinc-600 hover:bg-zinc-100 cursor-pointer'
            : 'text-zinc-300 cursor-not-allowed'
        ]"
        :disabled="!hasPrev"
        @click="goToPage(currentPage - 1)"
      >
        <ChevronLeft :size="14" />
        <span class="hidden sm:inline">Anterior</span>
      </button>

      <!-- Números de Página -->
      <template v-for="(page, index) in visiblePages" :key="index">
        <span
          v-if="page === 'ellipsis'"
          class="h-8 w-8 flex items-center justify-center text-xs text-zinc-300 select-none"
        >
          ...
        </span>
        <button
          v-else
          type="button"
          class="h-8 w-8 rounded-lg text-xs font-medium transition-colors cursor-pointer"
          :class="[
            page === currentPage
              ? 'bg-zinc-800 text-white'
              : 'text-zinc-500 hover:bg-zinc-100'
          ]"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
      </template>

      <!-- Próximo -->
      <button
        type="button"
        class="h-8 px-2.5 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
        :class="[
          hasNext
            ? 'text-zinc-600 hover:bg-zinc-100 cursor-pointer'
            : 'text-zinc-300 cursor-not-allowed'
        ]"
        :disabled="!hasNext"
        @click="goToPage(currentPage + 1)"
      >
        <span class="hidden sm:inline">Próximo</span>
        <ChevronRight :size="14" />
      </button>
    </div>
  </div>
</template>
