<script setup lang="ts">
import { ref, computed } from 'vue';
import { PackageSearch, Plus } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTab2 from '@/shared/components/ui/BaseTab2/BaseTab2.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import ProductCard from '@/modules/products/components/ProductCard.vue';
import ProductModal from '@/modules/products/components/ProductModal.vue';
import FornecedorTable from '../fornecedores/components/FornecedorTable.vue';
import FornecedorStats from '../fornecedores/components/FornecedorStats.vue';
import FornecedorFormModal from '../fornecedores/components/FornecedorFormModal.vue';

import { FILTER_CONFIG, TAB_OPTIONS } from '@/modules/products/constants/product.constants';
import { useProductModal } from '../composables/useProductModal';
import { useProductsQuery, useToggleProductActiveMutation } from '../composables/useProductsQuery';
import type { ProdutoRead } from '../types/products.types';
import { useFornecedorModal } from '../fornecedores/composables/useFornecedorModal';
import { useFornecedoresQuery } from '../fornecedores/composables/useFornecedoresQuery';
import { useToggleFornecedorAtivoMutation } from '../fornecedores/composables/useFornecedoresMutations';
import type { FornecedorReadType } from '../fornecedores/schemas/fornecedor.schema';

const { openCreateModal, openEditModal, openViewModal } = useProductModal();
const {
  openCreateModal: openCreateFornecedorModal,
  openEditModal: openEditFornecedorModal,
  openViewModal: openViewFornecedorModal,
} = useFornecedorModal();

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const activeTab = ref('product');
const searchTerm = ref<string | null>('');
const selectedFilter = ref<string | null>(null);

// Fornecedor
const {
  searchQuery: fornecedorSearch,
  activeFilterQuery: fornecedorFilter,
  fornecedores,
  stats: fornecedorStats,
  isLoading: isFornecedoresLoading,
  isError: isFornecedoresError,
} = useFornecedoresQuery();
const toggleFornecedorMutation = useToggleFornecedorAtivoMutation();
const isFornecedorToggleModalOpen = ref(false);
const fornecedorToToggle = ref<FornecedorReadType | null>(null);

const { data: products } = useProductsQuery(searchTerm);
const toggleMutation = useToggleProductActiveMutation();

const localOverrides = ref<Record<number, ProdutoRead>>({});

const mergedProducts = computed(() => {
  const base = products.value || [];
  const overrides = Object.values(localOverrides.value);
  const overridesById = new Map(overrides.map((item) => [item.id, item]));
  const merged = base.map((item) => overridesById.get(item.id) || item);
  const baseIds = new Set(base.map((item) => item.id));
  overrides.forEach((item) => {
    if (!baseIds.has(item.id)) merged.push(item);
  });
  return merged;
});

const filteredProducts = computed(() => {
  const term = (searchTerm.value || '').trim().toLowerCase();
  let list = mergedProducts.value;

  if (term) {
    list = list.filter((product) => {
      const nameMatch = product.nome?.toLowerCase().includes(term);
      const codeMatch = product.codigo_produto?.toLowerCase().startsWith(term);
      return nameMatch || codeMatch;
    });
  }

  if (selectedFilter.value === 'active') {
    list = list.filter((product) => product.ativo);
  } else if (selectedFilter.value === 'inactive') {
    list = list.filter((product) => !product.ativo);
  }

  return list;
});

const isSearchActive = computed(() => (searchTerm.value || '').trim().length > 0);
const isFilterActive = computed(() => !!selectedFilter.value);

const emptyState = computed(() => {
  if (isSearchActive.value || isFilterActive.value) {
    return {
      title: 'Nenhum produto encontrado',
      description: 'Ajuste a busca ou os filtros para ver outros resultados.',
      actionLabel: 'Limpar filtros',
      actionType: 'clear',
    };
  }

  return {
    title: 'Nenhum produto cadastrado',
    description: 'Comece cadastrando seu primeiro produto no catalogo.',
    actionLabel: 'Cadastrar produto',
    actionType: 'create',
  };
});

function getProductById(id: number) {
  return mergedProducts.value.find((product) => product.id === id);
}

function getProductImage(product: ProdutoRead) {
  const primary = product.fotos?.find((foto) => foto.principal);
  if (primary?.url) return primary.url;
  return product.fotos?.[0]?.url || '';
}

function handleAddClick() {
  if (activeTab.value === 'product') {
    openCreateModal();
  } else {
    openCreateFornecedorModal();
  }
}

function handleToggleFornecedor(fornecedor: FornecedorReadType) {
  fornecedorToToggle.value = fornecedor;
  isFornecedorToggleModalOpen.value = true;
}

function handleConfirmFornecedorToggle() {
  if (!fornecedorToToggle.value) return;
  toggleFornecedorMutation.mutate(fornecedorToToggle.value.id, {
    onSuccess: () => {
      isFornecedorToggleModalOpen.value = false;
      fornecedorToToggle.value = null;
    },
  });
}

function handleCloseFornecedorToggleModal() {
  isFornecedorToggleModalOpen.value = false;
  fornecedorToToggle.value = null;
}

function handleViewProduct(id: number) {
  const product = getProductById(id);
  if (product) openViewModal(product);
}

function handleEditProduct(id: number) {
  const product = getProductById(id);
  if (product) openEditModal(product);
}

function handleToggleProduct(id: number) {
  toggleMutation.mutate(id, {
    onSuccess: (data) => {
      localOverrides.value = {
        ...localOverrides.value,
        [data.id]: data,
      };
    },
  });
}

function handleEmptyAction() {
  if (emptyState.value.actionType === 'clear') {
    searchTerm.value = '';
    selectedFilter.value = null;
    return;
  }

  handleAddClick();
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        :title="activeTab === 'product' ? 'Estoque' : 'Fornecedores'"
        :description="activeTab === 'product' ? 'Gerencia os produtos no seu estoque' : 'Gerencie os fornecedores da sua empresa'"
      />

      <div class="flex gap-5">
        <BaseTab2 :options="TAB_OPTIONS" v-model="activeTab" />
        <BaseButton
          variant="primary"
          size="md"
          type="button"
          class="flex gap-1"
          @click="handleAddClick"
        >
          <Plus :size="20" />
          {{ activeTab === 'product' ? 'Adicionar Produto' : 'Adicionar Fornecedor' }}
        </BaseButton>
      </div>
    </div>

    <!-- Produtos Tab -->
    <template v-if="activeTab === 'product'">
      <div class="flex gap-5 p-4 bg-white rounded-2xl">
        <BaseSearchInput
          class="md:max-w-2/3 lg:max-w-1/2"
          v-model="searchTerm"
          placeholder="Buscar produto por nome ou código..."
        />
        <BaseFilter :filter-config="FILTER_CONFIG" v-model="selectedFilter" />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProductCard
          v-for="product in filteredProducts"
          :key="product.id"
          :id="product.id"
          :name="product.nome"
          :description="product.observacao || 'Sem descrição cadastrada'"
          :category="product.categoria || 'SEM CATEGORIA'"
          :price="product.estoque.valor_varejo / 100"
          :storage="product.estoque.quantidade || 0"
          :image_url="`${API_BASE_URL}/${getProductImage(product)}`"
          :status="product.ativo"
          @view="handleViewProduct"
          @edit="handleEditProduct"
          @toggle="handleToggleProduct"
        />
      </div>

      <div
        v-if="filteredProducts.length === 0"
        class="rounded-2xl border border-dashed border-zinc-200 bg-white p-10 text-center"
      >
        <div
          class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-primary/10 text-brand-primary"
        >
          <PackageSearch :size="28" />
        </div>
        <h3 class="text-base font-semibold text-zinc-800">{{ emptyState.title }}</h3>
        <p class="mt-1 text-sm text-zinc-400">{{ emptyState.description }}</p>
        <div class="mt-6 flex items-center justify-center">
          <BaseButton
            variant="primary"
            size="md"
            type="button"
            class="flex items-center gap-2"
            @click="handleEmptyAction"
          >
            <Plus v-if="emptyState.actionType === 'create'" :size="18" />
            {{ emptyState.actionLabel }}
          </BaseButton>
        </div>
      </div>
    </template>

    <!-- Fornecedores Tab -->
    <template v-else-if="activeTab === 'supplier'">
      <FornecedorStats
        :total="fornecedorStats.total"
        :ativos="fornecedorStats.ativos"
        :inativos="fornecedorStats.inativos"
        :loading="isFornecedoresLoading"
      />

      <FornecedorTable
        :fornecedores="fornecedores"
        :is-loading="isFornecedoresLoading"
        :is-error="isFornecedoresError"
        v-model:search="fornecedorSearch"
        v-model:status-filter="fornecedorFilter"
        @view="openViewFornecedorModal"
        @edit="openEditFornecedorModal"
        @toggle-status="handleToggleFornecedor"
      />
    </template>

    <ProductModal />
    <FornecedorFormModal />

    <BaseConfirmModal
      :is-open="isFornecedorToggleModalOpen"
      :title="(fornecedorToToggle?.ativo ? 'Desativar' : 'Ativar') + ' Fornecedor?'"
      :description="`Deseja realmente ${fornecedorToToggle?.ativo ? 'desativar' : 'ativar'} o fornecedor ${fornecedorToToggle?.nome}?`"
      :confirm-label="fornecedorToToggle?.ativo ? 'Desativar' : 'Ativar'"
      :variant="fornecedorToToggle?.ativo ? 'danger' : 'info'"
      @close="handleCloseFornecedorToggleModal"
      @confirm="handleConfirmFornecedorToggle"
    />
  </div>
</template>
