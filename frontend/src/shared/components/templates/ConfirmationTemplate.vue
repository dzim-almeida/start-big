<script setup lang="ts">
import type { Component } from 'vue';

interface Props {
  icon?: Component;
  iconBgClass?: string;
  iconColorClass?: string;
}

defineProps<Props>();
</script>

<template>
  <div class="flex flex-col items-center text-center py-4">
    <div
      v-if="icon"
      :class="['w-14 h-14 rounded-full flex items-center justify-center mb-4', iconBgClass]"
    >
      <component :is="icon" :size="28" :class="iconColorClass" />
    </div>

    <slot name="description" />
    <slot name="footer" />
  </div>
</template>
