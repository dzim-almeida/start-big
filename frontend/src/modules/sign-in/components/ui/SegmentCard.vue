<script setup lang="ts">
/**
 * @component SegmentCard
 * @description Card clicável para seleção de segmento de negócio.
 */
import type { SegmentOption } from '../../types/sign-in.types';
import SegmentIcons from '../icons/SegmentIcons.vue';

defineProps<{
  segment: SegmentOption;
  selected: boolean;
}>();

defineEmits<{
  select: [];
}>();
</script>

<template>
  <button
    type="button"
    class="p-4 rounded-xl border-2 text-left transition-all duration-200 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-brand-primary/50"
    :class="
      selected
        ? 'border-brand-primary bg-blue-50 shadow-md'
        : 'border-gray-200 hover:border-brand-primary/50'
    "
    @click="$emit('select')"
  >
    <div class="flex items-center gap-3">
      <div
        class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
        :class="selected ? 'bg-brand-primary text-white' : 'bg-gray-100 text-gray-600'"
      >
        <SegmentIcons :icon="segment.icon" :size="20" />
      </div>
      <div>
        <span
          class="font-semibold text-sm block"
          :class="selected ? 'text-brand-primary' : 'text-brand-action'"
        >
          {{ segment.label }}
        </span>
        <p class="text-xs text-gray-500">{{ segment.description }}</p>
      </div>
    </div>
  </button>
</template>
