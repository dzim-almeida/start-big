<script setup lang="ts">
import { computed } from 'vue';
import { ProductSaleListItem } from '../../schemas/productSale.schema';

import { formatCurrency } from '@/shared/utils/finance';

const props = defineProps<{
    product: ProductSaleListItem[number]
}>();

const emit = defineEmits<{
  click: []
}>();

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function handleClick() {
  emit('click');
}

const imgUrl = computed(() => {
    if (!props.product.imagem_url) return null;
    return `${API_BASE_URL}/${props.product.imagem_url}`;
})
</script>

<template>
  <div class="py-2 px-6 border-b-2 border-zinc-200 bg-white hover:bg-zinc-100 flex justify-between cursor-pointer group" @click="handleClick">
    <div class="flex-1 flex gap-4">
      <div class="w-20 h-20 rounded-2xl bg-brand-primary/30 group-hover:transition-transform group-hover:scale-105 transition-all">
        <img v-if="imgUrl" :src="imgUrl" :alt="product.nome" class="w-full h-full object-fit rounded-xl" />
        <div v-else class="w-full h-full flex items-center justify-center text-white group-hover:text-lg transition-all">
          {{ product.nome.charAt(0).toUpperCase() }}
        </div>
      </div>
      <div>
        <h1 class="font-poppins font-semibold text-md text-zinc-800 group-hover:text-brand-primary">{{ product.nome }}</h1>
        <p class="font-poppins font-semibold text-xs text-zinc-500">{{ `SKU: ${product.sku}` }}</p>
      </div>
    </div>
    <div class="flex flex-col items-end justify-between">
        <p 
          :class="[
            'py-1 px-3 w-fit bg-brand-primary/10 rounded-md font-poppins font-bold text-xs text-brand-primary center'
          ]"
        >
          {{ `Estoque: ${product.estoque} un.` }}
        </p>
        <p class="mb-2 font-poppins font-bold text-xl text-brand-primary">
          {{ formatCurrency(product.preco) }}
        </p>
    </div>
  </div>
</template>
