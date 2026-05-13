import { computed, ref, watch } from 'vue';
import { refDebounced } from '@vueuse/core';

import { useProductQuery } from './queries/useProductQuery';
import { useAddItemSaleMutation } from './mutates/useItemSaleMutation';

import type { ProductSaleCreate } from '../schemas/productSale.schema';

export function useProductSearch() {
  const inputOnFocus = ref(false);
  
  function handleInputChange(isSearching: boolean) {
    inputOnFocus.value = isSearching;
  }

  const searchTerm = ref('');
  const debouncedSearchTerm = refDebounced(searchTerm, 300);

  const selectedProductId = ref<number | null>(null);
  const selectedProductName = ref<string | null>(null);

  const quantity = ref(1);

  const productQuery = useProductQuery(debouncedSearchTerm);
  const addItemSaleMutation = useAddItemSaleMutation();

  const isSearching = computed(() => {
    return (
      debouncedSearchTerm.value.trim().length > 1 &&
      selectedProductId.value === null
    );
  });

  const canAddItem = computed(() => {
    return !!selectedProductId.value && quantity.value > 0;
  });

  function selectProduct(productName: string, productId: number) {
    inputOnFocus.value = false;
    searchTerm.value = productName;
    selectedProductName.value = productName;
    selectedProductId.value = productId;
    quantity.value = 1;
  }

  function increaseQuantity() {
    quantity.value += 1;
  }

  function decreaseQuantity() {
    if (quantity.value > 1) {
      quantity.value -= 1;
    }
  }

  function resetSelection() {
    searchTerm.value = '';
    selectedProductName.value = null;
    selectedProductId.value = null;
    quantity.value = 1;
    inputOnFocus.value = false;
  }

  function addItemToSale(saleId: number | null) {
    if (!saleId || !selectedProductId.value || quantity.value <= 0) {
      return;
    }

    const payload: ProductSaleCreate = {
      tipo_produto: 'CADASTRADO',
      quantidade: quantity.value,
      produto_id: selectedProductId.value,
    };

    addItemSaleMutation.mutate(
      {
        saleId,
        payload,
      },
      {
        onSuccess: () => {
          resetSelection();
        },
      },
    );
  }

  watch(searchTerm, (term) => {
    if (!selectedProductId.value) return;

    if (term !== selectedProductName.value) {
      selectedProductId.value = null;
      selectedProductName.value = null;
      quantity.value = 1;
    }
  });

  return {
    searchTerm,
    debouncedSearchTerm,

    products: productQuery.data,
    isLoading: productQuery.isLoading,
    isFetching: productQuery.isFetching,

    selectedProductId,
    selectedProductName,
    quantity,

    isSearching,
    canAddItem,
    isAddingItem: addItemSaleMutation.isPending,

    handleInputChange,
    selectProduct,
    increaseQuantity,
    decreaseQuantity,
    resetSelection,
    addItemToSale,
  };
}