<script setup lang="ts">
import { Funnel, Check } from 'lucide-vue-next';

import { FilterOption } from '@/shared/types/filter.types';
import { ref } from 'vue';

interface Props {
  filterConfig: Record<string, FilterOption>;
  title?: string;
  buttonLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Filtrar por Status',
  buttonLabel: 'Filtros',
});

const selectedFilter = defineModel<string | null>();

const isFilterMenuOpen = ref<boolean>(false);

function toggleFilterMenu() {
  isFilterMenuOpen.value = !isFilterMenuOpen.value;
}

function selectFilter(filter: string | null) {
    isFilterMenuOpen.value = false;
    selectedFilter.value = filter;
}
</script>

<template>
  <div class="relative">
    <button
      @click="toggleFilterMenu()"
      :class="[
        'flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs md:text-sm font-semibold border transition-all cursor-pointer select-none',
        selectedFilter
          ? 'bg-brand-primary/10 text-brand-primary border-brand-primary'
          : 'text-zinc-600 border-brand-grey hover:text-brand-primary/80 hover:border-brand-primary/80',
      ]"
    >
      <Funnel :size="20" />
      {{ props.buttonLabel }}
      <span v-if="selectedFilter" class="ml-1 w-2 h-2 rounded-full bg-brand-primary"></span>
    </button>

    <!-- Filter Dropdown -->
    <div
      v-if="isFilterMenuOpen"
      class="absolute top-full right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-zinc-100 z-50 p-2"
    >
      <div class="text-[10px] uppercase font-bold text-zinc-400 px-2 py-2">
        {{ props.title }}
      </div>

      <button
        @click="selectFilter(null)"
        class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
      >
        Todos
        <Check v-if="selectedFilter === null" :size="16" class="text-brand-primary" />
      </button>

      <button
        v-for="(config, key) in filterConfig"
        :key="key"
        @click="selectFilter(key)"
        class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
      >
        <div class="flex items-center gap-2">
          <span
            :class="[
              'w-2 h-2 rounded-full',
              config.color
            ]"
          ></span>
          {{ config.label }}
        </div>
        <Check v-if="selectedFilter === key" :size="16" class="text-brand-primary" />
      </button>
    </div>
  </div>
</template>
