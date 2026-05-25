<script setup lang="ts">
import { ShoppingCart } from 'lucide-vue-next';

import StatusPulse from '../icons/StatusPulse.vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const props = defineProps<{
  companyName: string;
  imageUrl?: string;
  status: boolean;
  isLoading: boolean;
}>();
</script>

<template>
  <div 
    v-if="isLoading"
    class="flex items-center space-x-3 bg-zinc-900 p-3 rounded-2xl border border-zinc-800 animate-pulse select-none cursor-wait"
  >
    <div class="w-10 h-10 bg-zinc-800 rounded-lg shadow-inner"></div>

    <div class="flex-1 min-w-0 space-y-2">
      <div class="h-4 bg-zinc-800 rounded w-3/5"></div>
      <div class="h-3 bg-zinc-800 rounded w-2/5"></div>
    </div>
  </div>

  <div 
    v-else
    class="flex items-center space-x-3 bg-zinc-900 p-3 rounded-2xl border border-zinc-800"
  >
    <div
      class="w-10 h-10 rounded-lg flex items-center justify-center shadow-inner"
      :class="imageUrl ? '' : 'bg-brand-primary'"
    >
      <img
        v-if="imageUrl"
        :src="`${API_BASE_URL}/${imageUrl}`"
        alt="Logo da Empresa"
        class="w-full h-full object-cover rounded-lg"
      />
      <ShoppingCart
        v-else
        :size="22"
        class="text-white"
      />
    </div>

    <div class="flex-1">
      <h1 class="text-sm font-bold -tracking-normal uppercase -mb-1">{{companyName}}</h1>
      <div class="flex justify-start items-center space-x-1 mt-1">
        <StatusPulse :status="status" />
        <span class="text-[10px] text-zinc-500 font-medium uppercase">
            {{ status ? 'sistema ativo' : 'sistema desativado' }}
        </span>
      </div>
    </div>
  </div>
</template>
