<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
}>();
</script>

<template>
  <div
    class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl text-left transition-all duration-300 select-none hover:p-5 hover:bg-blue-50 hover:shadow-sm"
  >
    <!-- Ícone -->
    <div class="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center shrink-0">
      <slot></slot>
    </div>

    <!-- Texto -->
    <div>
      <h3 class="font-semibold text-brand-action text-sm">{{ title }}</h3>
      <p class="text-gray-500 text-xs">{{ description }}</p>
    </div>
  </div>
</template>
