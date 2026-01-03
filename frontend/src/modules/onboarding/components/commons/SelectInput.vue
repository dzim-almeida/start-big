<script setup lang="ts">
import Icons from '../icons/Icons.vue';

interface option {
  label: string;
  value: string;
}

defineProps<{
  options: option[];
}>();

const emit = defineEmits<{
  select: [value: string];
}>();

function changeSelect(value: string) {
  emit('select', value);
}
</script>

<template>
  <div class="relative h-fit">
    <select
      :value="options[0].value"
      @change="changeSelect(($event.target as HTMLSelectElement).value)"
      class="h-full px-3 py-2 border border-gray-300 rounded-md bg-white text-sm text-gray-700 focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary cursor-pointer appearance-none pr-8"
    >
      <option v-for="(option, index) in options" :key="index" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <div class="absolute right-2 top-1/2 -translate-y-1/2">
      <Icons icon="select" />
    </div>
  </div>
</template>
