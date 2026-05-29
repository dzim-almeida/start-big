<script setup lang="ts">
defineProps<{
    title: string;
    description: string;
    isLoading?: boolean;
}>();
</script>

<template>
  <div v-if="isLoading" class="py-5 w-80 bg-zinc-500 rounded-md animate-pulse"></div>
  <div v-else>
    <h2 class="text-xl md:text-2xl font-bold text-zinc-900">{{ title }}</h2>
    <p class="text-zinc-500 text-xs md:text-xs mt-0.5">
      {{description}}
    </p>
  </div>
</template>
