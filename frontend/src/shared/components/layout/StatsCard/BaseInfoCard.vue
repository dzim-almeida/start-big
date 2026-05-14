<script setup lang="ts">
import type { Component } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';

defineProps<{
icon?: Component;
title: string;
}>();
</script>

<template>
    <div class="w-full bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:border-brand-primary/30 transition-colors group relative">
        <div class="bg-slate-50 px-4 py-2 border-b border-slate-100 flex items-center">
            <LucideIcon :icon="icon" size="uxs" class="text-brand-primary" v-if="icon" />
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">{{ title }}</span>
        </div>
        <slot />
    </div>
</template>