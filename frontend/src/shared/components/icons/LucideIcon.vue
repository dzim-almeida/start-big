<script setup lang="ts">
import type { Component } from 'vue';

type size = 'sm' | 'md' | 'lg';

interface Props {
  icon: Component;
  size?: size;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'sm',
});

const sizes: Record<string, number> = {
  sm: 20,
  md: 24,
  lg: 30,
};
</script>

<template>
  <component class="mx-2" :is="icon" :size="sizes[size]"></component>
</template>
