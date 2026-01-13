<script setup lang="ts">
import { ArrowUpRight, ArrowDownRight } from 'lucide-vue-next';
import type { Component } from 'vue';

interface Props {
  icon: Component;
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
}

defineProps<Props>();
</script>

<template>
  <div
    class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5 group"
  >
    <!-- Header: Icon + Change Badge -->
    <div class="flex items-center justify-between mb-4">
      <div
        class="w-10 h-10 md:w-12 md:h-12 bg-zinc-50 rounded-xl md:rounded-2xl flex items-center justify-center border border-zinc-100 group-hover:bg-brand-primary/5 group-hover:border-brand-primary/20 transition-colors"
      >
        <component :is="icon" :size="20" class="text-zinc-900 md:w-6 md:h-6" />
      </div>
      <div
        :class="[
          'flex items-center gap-0.5 px-2 py-1 rounded-lg text-[10px] md:text-[11px] font-bold transition-transform group-hover:scale-105',
          isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600',
        ]"
      >
        <ArrowUpRight v-if="isPositive" :size="14" />
        <ArrowDownRight v-else :size="14" />
        <span>{{ change }}</span>
      </div>
    </div>

    <!-- Label -->
    <p class="text-zinc-500 text-[10px] md:text-xs font-semibold mb-1 uppercase tracking-wider">
      {{ label }}
    </p>

    <!-- Value -->
    <p class="text-xl md:text-2xl font-black text-zinc-900 tracking-tight">
      {{ value }}
    </p>
  </div>
</template>
