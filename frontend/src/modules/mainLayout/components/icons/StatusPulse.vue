<script setup lang="ts">
defineProps<{
  status: boolean;
}>();
</script>

<template>
  <div
    class="w-1.5 h-1.5 rounded-full animate-pulse"
    :class="status ? 'bg-green-500' : 'bg-red-500'"
  ></div>
</template>
