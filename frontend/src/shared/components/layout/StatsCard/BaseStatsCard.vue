<script setup lang="ts">
import type { Component } from 'vue';

interface Props {
  icon: Component;
  label: string;
  value: string;
}

defineProps<Props>();
</script>

<template>
  <div
    class="bg-white p-5 md:p-6 rounded-2xl md:rounded-3xl border border-zinc-200 hover:border-brand-secondary shadow-sm hover:shadow-md hover:shadow-brand-primary/10 transition-all duration-300 hover:-translate-y-0.5 group"
  >
    <!-- Header: Icon + Change Badge -->
    <div class="flex items-center justify-between mb-4">
      <div
        class="w-10 h-10 md:w-12 md:h-12 bg-zinc-50 rounded-xl md:rounded-2xl flex items-center justify-center border border-zinc-100 group-hover:bg-brand-primary/5 group-hover:border-brand-primary/20 transition-colors"
      >
        <component :is="icon" :size="20" class="text-zinc-900 md:w-6 md:h-6" />
      </div>
      <slot name="badge" />
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
