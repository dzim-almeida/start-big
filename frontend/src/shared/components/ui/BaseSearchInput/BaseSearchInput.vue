<script setup lang="ts">
import { Search } from 'lucide-vue-next'
</script>

<template>
  <div class="flex items-center space-x-4 flex-1">
    <div class="relative w-96">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" :size="18" />
      <input
        type="text"
        placeholder="Buscar produtos, vendas ou clientes..."
        class="w-full bg-zinc-100 border-none rounded-xl py-2.5 pl-10 pr-4 text-sm focus:ring-2 focus:ring-blue-500 transition-all outline-none"
      />
    </div>
  </div>
</template>
