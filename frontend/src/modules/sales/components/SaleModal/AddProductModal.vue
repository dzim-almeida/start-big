<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { PackageSearch, ArchiveX, ShoppingCart, Plus, Minus, Check } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';

import { useProductSearch } from '../../composables/flows/useProductSearch';
import { formatCurrency } from '@/shared/utils/finance';
import type { ProductSaleRead } from '../../schemas/productSale.schema';

const props = defineProps<{
  isOpen: boolean;
  saleId: number | null;
  isOrcamento?: boolean;
  currentItems?: ProductSaleRead[];
}>();

const emit = defineEmits<{
  close: [];
}>();

const currentItemsRef = computed(() => props.currentItems);
const searchContainerRef = ref<HTMLElement | null>(null);

const {
  searchTerm,
  products,
  isLoading,
  selectedProductId,
  selectedProductName,
  canAddItem,
  isAddingItem,
  quantity,
  handleInputChange,
  selectProduct,
  increaseQuantity,
  decreaseQuantity,
  addItemToSale,
  resetSelection,
} = useProductSearch(props.isOrcamento, currentItemsRef, searchContainerRef);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

watch(
  () => props.isOpen,
  (open) => {
    if (!open) {
      resetSelection();
    } else {
      nextTick(() => {
        const input = searchContainerRef.value?.querySelector('input');
        input?.focus();
      });
    }
  },
);

function getEstoqueStatus(product: { estoque: number; quantidade_minima?: number | null }) {
  if (product.estoque <= 0) return 'sem_estoque';
  if (product.quantidade_minima != null && product.estoque <= product.quantidade_minima) return 'baixo';
  return 'normal';
}

function handleProductClick(product: { nome: string; id: number; estoque: number }) {
  if (product.estoque <= 0) return;
  selectProduct(product.nome, product.id);
}

function handleAdd() {
  addItemToSale(props.saleId, false);
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Adicionar Produto" size="2xl" @close="emit('close')">
    <!-- Área de busca + lista: tudo dentro do searchContainerRef para não disparar onClickOutside ao clicar nos produtos -->
    <div ref="searchContainerRef" class="flex flex-col gap-3">
      <BaseSearchInput
        v-model="searchTerm"
        placeholder="Buscar por nome, código ou SKU..."
        @focusChange="handleInputChange"
      />

      <!-- Lista de produtos -->
      <div class="rounded-xl border border-zinc-200 overflow-hidden" style="min-height: 260px; max-height: 50vh; overflow-y: auto">
        <!-- Carregando -->
        <div v-if="isLoading" class="flex items-center justify-center py-16">
          <div class="h-8 w-8 animate-spin rounded-full border-4 border-zinc-300 border-t-brand-primary" />
        </div>

        <!-- Estado inicial -->
        <div
          v-else-if="!searchTerm.trim()"
          class="flex flex-col items-center justify-center py-16 gap-3 text-zinc-400"
        >
          <PackageSearch :size="40" class="opacity-50" />
          <div class="text-center">
            <p class="text-sm font-semibold text-zinc-500">Digite para buscar</p>
            <p class="text-xs text-zinc-400 mt-0.5">Busque por nome, SKU ou código de barras</p>
          </div>
        </div>

        <!-- Sem resultados -->
        <div
          v-else-if="products.length === 0"
          class="flex flex-col items-center justify-center py-16 gap-3 text-zinc-400"
        >
          <ArchiveX :size="40" class="opacity-50" />
          <p class="text-sm font-semibold">Nenhum produto encontrado</p>
        </div>

        <!-- Linhas de produto -->
        <div
          v-for="product in products"
          :key="product.id"
          :class="[
            'flex items-center gap-4 px-4 py-3 border-b border-zinc-100 last:border-b-0 transition-colors select-none',
            product.estoque <= 0
              ? 'opacity-50 cursor-not-allowed bg-zinc-50'
              : selectedProductId === product.id
              ? 'bg-brand-primary/5 cursor-pointer'
              : 'hover:bg-zinc-50 cursor-pointer',
          ]"
          @click="handleProductClick(product)"
        >
          <!-- Thumbnail -->
          <div
            class="h-12 w-12 shrink-0 rounded-lg overflow-hidden border border-zinc-200 bg-zinc-100 flex items-center justify-center"
          >
            <img
              v-if="product.imagem_url"
              :src="`${API_BASE_URL}/${product.imagem_url}`"
              :alt="product.nome"
              class="h-full w-full object-cover"
            />
            <span v-else class="text-base font-bold text-zinc-400">
              {{ product.nome.charAt(0).toUpperCase() }}
            </span>
          </div>

          <!-- Nome + SKU -->
          <div class="flex-1 min-w-0">
            <p
              :class="[
                'text-sm font-semibold truncate',
                selectedProductId === product.id ? 'text-brand-primary' : 'text-zinc-800',
              ]"
            >
              {{ product.nome }}
            </p>
            <p class="text-xs text-zinc-400 mt-0.5">SKU: {{ product.sku ?? '—' }}</p>
          </div>

          <!-- Badge de estoque -->
          <span
            :class="[
              'px-2 py-1 rounded-md text-[11px] font-semibold shrink-0',
              getEstoqueStatus(product) === 'sem_estoque'
                ? 'bg-red-100 text-red-600'
                : getEstoqueStatus(product) === 'baixo'
                ? 'bg-orange-100 text-orange-600'
                : 'bg-blue-50 text-blue-600',
            ]"
          >
            {{ product.estoque <= 0 ? 'Sem estoque' : `${product.estoque} em estoque` }}
          </span>

          <!-- Preço -->
          <p class="text-base font-bold text-brand-primary shrink-0 w-24 text-right">
            {{ formatCurrency(product.preco) }}
          </p>

          <!-- Indicador de selecionado -->
          <div
            :class="[
              'w-6 h-6 shrink-0 rounded-full flex items-center justify-center transition-colors',
              selectedProductId === product.id ? 'bg-brand-primary' : 'bg-zinc-100',
            ]"
          >
            <Check
              :size="12"
              :class="selectedProductId === product.id ? 'text-white' : 'text-zinc-300'"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Rodapé -->
    <template #footer>
      <!-- Produto selecionado: mostra nome + qtde + botão -->
      <div v-if="selectedProductId" class="flex items-center gap-4 w-full">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-zinc-800 truncate">{{ selectedProductName }}</p>
          <p class="text-xs text-zinc-400">Produto selecionado</p>
        </div>

        <!-- Stepper de quantidade -->
        <div class="flex items-center border border-zinc-200 rounded-lg overflow-hidden">
          <button
            type="button"
            :disabled="quantity <= 1"
            class="w-9 h-9 flex items-center justify-center text-zinc-500 hover:bg-zinc-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            @click="decreaseQuantity"
          >
            <Minus :size="16" />
          </button>
          <span class="min-w-10 text-center text-sm font-bold text-zinc-800 select-none px-1">
            {{ quantity }}
          </span>
          <button
            type="button"
            class="w-9 h-9 flex items-center justify-center text-zinc-500 hover:bg-zinc-100 transition-colors"
            @click="increaseQuantity"
          >
            <Plus :size="16" />
          </button>
        </div>

        <BaseButton variant="secondary" class="px-4" @click="emit('close')">Fechar</BaseButton>

        <BaseButton
          variant="primary"
          :is-loading="isAddingItem"
          :disabled="!canAddItem"
          class="gap-2"
          @click="handleAdd"
        >
          <ShoppingCart :size="16" />
          Adicionar ao Carrinho
        </BaseButton>
      </div>

      <!-- Sem produto selecionado -->
      <div v-else class="flex justify-end w-full">
        <BaseButton variant="secondary" class="px-5" @click="emit('close')">Fechar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
