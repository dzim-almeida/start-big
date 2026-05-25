<script setup lang="ts">
import { Search } from 'lucide-vue-next'

defineProps<{
  placeholder?: string;
}>();

const model = defineModel()
</script>

<template>
  <div class="flex items-center space-x-4 flex-1">
    <div class="relative w-full border border-brand-grey rounded-xl hover:border-brand-primary/80 transition-all">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 focus:text-brand-primary :" :size="18" />
      <input
        v-model="model"
        type="text"
        :placeholder="placeholder"
        class="w-full border-none rounded-xl py-2.5 pl-10 pr-4 text-sm focus:ring-2 focus:ring-brand-primary transition-all outline-none"
      />
    </div>
  </div>
</template>
