<script setup lang="ts">
interface Option {
  id: string;
  label: string;
}

defineProps<{
  options: Option[];
}>();

const model = defineModel();
</script>

<template>
  <div
    class="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm text-xs font-semibold self-start sm:self-auto"
  >
    <button
      v-for="opt in options"
      :key="opt.id"
      :class="[
        'px-3 md:px-4 py-1.5 md:py-2 rounded-lg transition-all duration-200',
        model === opt.id
          ? 'bg-zinc-900 text-white shadow-sm'
          : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50',
      ]"
      @click="model = opt.id"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
