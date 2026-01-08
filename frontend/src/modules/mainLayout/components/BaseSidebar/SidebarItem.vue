<script setup lang="ts">
import { sidebarLabelOptions } from '@/shared/types/mainLayout.types';
import type { Component } from 'vue';

const props = defineProps<{
  id: string;
  icon: Component;  
  label: sidebarLabelOptions;
  active: boolean;
  route: string;
}>();

const emit = defineEmits<{
    clickTab: [id: string, label: sidebarLabelOptions, route: string]
}>();

function handleClick(): void {
    emit('clickTab', props.id, props.label, props.route);
}
</script>
<template>
  <button
    @click="handleClick"
    class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 group cursor-pointer"
    :class="[
        active 
        ? 'bg-brand-primary text-white shadow-lg shadow-blue-900/15' 
        : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
    ]"
  >
    <component :is="icon" :size="20" />
    <span class="font-medium text-sm">{{label}}</span>
    <div
        v-if="active"
        class="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse"
    >
    </div>
  </button>
</template>
