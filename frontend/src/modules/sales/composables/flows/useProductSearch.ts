import { computed, nextTick, ref, watch, type Ref } from 'vue';
import { refDebounced, onClickOutside } from '@vueuse/core';

import { useProductQuery } from '../queries/useProductQuery';
import { useAddItemSaleMutation, useUpdateItemSaleMutation } from '../mutates/useItemSaleMutation';
import { useAddItemOrcamentoMutation } from '../mutates/useItemOrcamentoMutation';

import type { ProductSaleCreate, ProductSaleRead, ProductSaleListItem } from '../../schemas/productSale.schema';

export function useProductSearch(
  isOrcamento = false,
  currentItems?: Ref<ProductSaleRead[] | undefined>,
  externalContainerRef?: Ref<HTMLElement | null>,
) {
  const inputOnFocus = ref(false);

  function handleInputChange(isSearching: boolean) {
    inputOnFocus.value = isSearching;
  }

  const searchTerm = ref('');
  const debouncedSearchTerm = refDebounced(searchTerm, 300);

  const selectedProductId = ref<number | null>(null);
  const selectedProductName = ref<string | null>(null);

  const quantity = ref(1);
  const desconto = ref(0);
  const selectedProduct = ref<ProductSaleListItem[number] | null>(null);
  const highlightedIndex = ref(-1);

  const productQuery = useProductQuery(debouncedSearchTerm);
  const addItemSaleMutation = useAddItemSaleMutation();
  const addItemOrcamentoMutation = useAddItemOrcamentoMutation();
  const updateItemSaleMutation = useUpdateItemSaleMutation();

  const searchContainerRef: Ref<HTMLElement | null> = externalContainerRef ?? ref<HTMLElement | null>(null);
  const quantityInputRef = ref<{ focus: () => void } | null>(null);

  const isSearching = computed(() => {
    return (
      searchTerm.value.trim().length > 1 &&
      debouncedSearchTerm.value.trim().length > 1 &&
      selectedProductId.value === null
    );
  });

  const canAddItem = computed(() => {
    return !!selectedProductId.value && quantity.value > 0;
  });

  const totalItem = computed(() => {
    if (!selectedProduct.value) return 0;
    const subtotal = selectedProduct.value.preco * quantity.value;
    return Math.max(0, subtotal - desconto.value);
  });

  // Ordenar: produtos sem estoque vão para o final
  const sortedProducts = computed(() => {
    if (!productQuery.data.value) return [];
    return [...productQuery.data.value].sort((a, b) => {
      const aOut = a.estoque <= 0 ? 1 : 0;
      const bOut = b.estoque <= 0 ? 1 : 0;
      return aOut - bOut;
    });
  });

  function selectProduct(productName: string, productId: number) {
    inputOnFocus.value = false;
    searchTerm.value = productName;
    selectedProductName.value = productName;
    selectedProductId.value = productId;
    quantity.value = 1;
    desconto.value = 0;
    highlightedIndex.value = -1;
    selectedProduct.value = sortedProducts.value.find((p) => p.id === productId) ?? null;
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
    selectedProduct.value = null;
    quantity.value = 1;
    desconto.value = 0;
    inputOnFocus.value = false;
    highlightedIndex.value = -1;
  }

  function focusSearchInput() {
    nextTick(() => {
      const input = searchContainerRef.value?.querySelector('input');
      input?.focus();
    });
  }

  function addItemToSale(saleId: number | null, autoAdd = false) {
    if (!saleId || !selectedProductId.value || quantity.value <= 0) {
      return;
    }

    const onSuccessCallback = () => {
      resetSelection();
      focusSearchInput();
    };

    // Verificar se o produto já existe na venda
    const existingItem = currentItems?.value?.find(
      (item) => item.produto_id === selectedProductId.value,
    );

    if (existingItem && !isOrcamento) {
      const novaQtd = autoAdd
        ? existingItem.quantidade + 1
        : existingItem.quantidade + quantity.value;

      updateItemSaleMutation.mutate(
        {
          saleId,
          productId: existingItem.id,
          payload: {
            quantidade: novaQtd,
            ...(desconto.value > 0 && { desconto: desconto.value }),
          },
        },
        { onSuccess: onSuccessCallback },
      );
      return;
    }

    const payload: ProductSaleCreate = {
      tipo_produto: 'CADASTRADO',
      quantidade: autoAdd ? 1 : quantity.value,
      produto_id: selectedProductId.value,
      ...(desconto.value > 0 && { desconto: desconto.value }),
    };

    if (isOrcamento) {
      addItemOrcamentoMutation.mutate(
        { orcamentoId: saleId, payload },
        { onSuccess: onSuccessCallback },
      );
    } else {
      addItemSaleMutation.mutate(
        { saleId, payload },
        { onSuccess: onSuccessCallback },
      );
    }
  }

  // Navegação por teclado
  function handleKeydown(e: KeyboardEvent) {
    if (!isSearching.value) {
      if (e.key === 'Enter' && selectedProductId.value) {
        e.preventDefault();
        // Disparar pelo caller — addItemToSale é chamado externamente
      }
      return;
    }

    const products = sortedProducts.value;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (highlightedIndex.value < products.length - 1) {
          highlightedIndex.value++;
          scrollToHighlighted();
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (highlightedIndex.value > 0) {
          highlightedIndex.value--;
          scrollToHighlighted();
        }
        break;

      case 'Enter':
        e.preventDefault();
        if (highlightedIndex.value >= 0 && highlightedIndex.value < products.length) {
          const product = products[highlightedIndex.value];
          if (product.estoque > 0) {
            selectProduct(product.nome, product.id);
            nextTick(() => quantityInputRef.value?.focus?.());
          }
        }
        break;

      case 'Escape':
        e.preventDefault();
        resetSelection();
        break;
    }
  }

  function scrollToHighlighted() {
    nextTick(() => {
      const el = document.querySelector(`[data-product-index="${highlightedIndex.value}"]`);
      el?.scrollIntoView({ block: 'nearest' });
    });
  }

  onClickOutside(searchContainerRef, () => {
    if (isSearching.value) {
      resetSelection();
    }
  });

  // Reset highlight quando a lista de produtos muda
  watch(sortedProducts, () => {
    highlightedIndex.value = -1;
  });

  watch(searchTerm, (term) => {
    if (!selectedProductId.value) return;

    if (term !== selectedProductName.value) {
      selectedProductId.value = null;
      selectedProductName.value = null;
      selectedProduct.value = null;
      quantity.value = 1;
      desconto.value = 0;
    }
  });

  return {
    searchTerm,
    debouncedSearchTerm,

    products: sortedProducts,
    isLoading: productQuery.isLoading,
    isFetching: productQuery.isFetching,

    selectedProductId,
    selectedProductName,
    selectedProduct,
    quantity,
    desconto,
    totalItem,
    searchContainerRef,
    quantityInputRef,
    highlightedIndex,

    isSearching,
    canAddItem,
    isAddingItem: computed(() =>
      isOrcamento
        ? addItemOrcamentoMutation.isPending.value
        : addItemSaleMutation.isPending.value || updateItemSaleMutation.isPending.value,
    ),

    handleInputChange,
    handleKeydown,
    selectProduct,
    increaseQuantity,
    decreaseQuantity,
    resetSelection,
    addItemToSale,
  };
}
