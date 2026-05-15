<script setup lang="ts">
import { ArchiveX } from 'lucide-vue-next';

import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import ProductOption from './ProductOption.vue';

import { useProductSearch } from '../../composables/flows/useProductSearch';
import { useItemModal } from '../../composables/flows/useItemModal';
import UnitValueInput from './UnitValueInput.vue';

defineProps<{
  saleId: number | null;
}>()

const {
  searchTerm,
  isSearching,
  products,
  isLoading,
  selectedProductId,
  canAddItem,
  isAddingItem,
  quantity,
  handleInputChange,
  selectProduct,
  increaseQuantity,
  decreaseQuantity,
  addItemToSale,
  resetSelection
} = useProductSearch();

const { openCreateItemModal } = useItemModal();

function handleAddAvulso() {
  resetSelection();
  openCreateItemModal();
}
</script>

<template>
  <div class="w-full flex gap-4">
    <div class="relative w-full md:max-w-1/2">
      <BaseSearchInput v-model="searchTerm" placeholder="Digite o nome ou código do produto" @focusChange="handleInputChange" />

      <div
        v-if="isSearching"
        class="absolute left-0 top-full z-50 mt-2 w-full min-h-20 rounded-xl shadow-lg bg-zinc-50"
      >
        <div
          :class="[
            'w-full py-3 px-6 select-none',
            products?.length ? 'border-b-2 border-zinc-200' : '',
          ]"
        >
          <p class="font-poppins font-semibold text-[10px] uppercase text-mid-gray">
            {{ `Produtos encontrados (${products?.length || 0})` }}
          </p>
        </div>

        <div class="w-full min-h-20 bg-white flex items-center justify-center">
          <div
            v-if="isLoading"
            class="h-8 w-8 animate-spin rounded-full border-4 border-zinc-300 border-t-brand-primary"
          ></div>
          <div v-else-if="products?.length == 0" class="py-5 flex flex-col items-center">
            <ArchiveX :size="30" class="text-mid-gray" />
            <p class="mt-1 font-poppins font-semibold text-xs text-mid-gray">
              Nenhum produto encontrado
            </p>
          </div>
          <div v-else class="w-full">
            <ProductOption
              v-for="product in products"
              :key="product.id"
              :product="product"
              @click="selectProduct(product.nome, product.id)"
            />
          </div>
        </div>

        <div>
          <div class="w-full py-3 px-6">
            <p class="font-poppins font-bold text-[10px] text-mid-gray">
              Não encontrou o produto?
              <span
                class="font-poppins font-semibold text-[10px] text-brand-primary/90 hover:underline cursor-pointer"
                @click="handleAddAvulso"
              >
                Adicionar produto avulso
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <label class="font-poppins font-semibold text-xs">Qtde.</label>
      <div class="w-32 h-full">
        <UnitValueInput v-model="quantity" :disabled="!selectedProductId" @increase="increaseQuantity" @decrease="decreaseQuantity" />
      </div>
      
    </div>
    <BaseButton size="sm" :disabled="!canAddItem || isAddingItem" @click="addItemToSale(saleId)">
      Adicionar Produto
    </BaseButton>
  </div>
</template>
