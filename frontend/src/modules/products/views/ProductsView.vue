<script setup lang="ts">
import { ref } from 'vue';
import { Plus } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTab2 from '@/shared/components/ui/BaseTab2/BaseTab2.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import ProductCard from '@/modules/products/components/ProductCard.vue';
import ProductModal from '@/modules/products/components/ProductModal.vue';  

import { FILTER_CONFIG, TAB_OPTIONS } from '@/modules/products/constants/product.constants';
import { useProductModal } from '../composables/useProductModal';

const { openModal } = useProductModal();

const activeTab = ref('product');
const searchTerm = ref<string | null>(null);
const selectedFilter = ref<string | null>(null);

// Mock product data
const products = ref([
  {
    id: 1,
    name: 'Mouse Gamer 12000 DPI',
    description: '6 Botões programáveis, sensor óptico de alta precisão.',
    category: 'PERIFÉRICOS',
    price: 120.0,
    storage: 45,
    image_url: 'https://images.unsplash.com/photo-1527814050087-3793815479db?w=400&h=400&fit=crop',
    status: true,
  },
  {
    id: 2,
    name: 'Monitor 27" IPS 144Hz',
    description: '1ms de resposta, HDR10, bordas ultrafinas.',
    category: 'ELETRÔNICOS',
    price: 1400.0,
    storage: 2,
    image_url: 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=400&fit=crop',
    status: true,
  },
  {
    id: 3,
    name: 'Headset Wireless 7.1',
    description: 'Cancelamento de ruído, bateria de 20h.',
    category: 'PERIFÉRICOS',
    price: 550.0,
    storage: 0,
    image_url: 'https://images.unsplash.com/photo-1599669454699-248893623440?w=400&h=400&fit=crop',
    status: false,
  },
  {
    id: 4,
    name: 'Teclado Mecânico RGB',
    description: 'Switch blue, iluminação personalizável, ABNT2.',
    category: 'PERIFÉRICOS',
    price: 350.0,
    storage: 18,
    image_url: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=400&fit=crop',
    status: true,
  },
  {
    id: 5,
    name: 'Webcam Full HD 1080p',
    description: 'Microfone integrado, foco automático, 60fps.',
    category: 'ELETRÔNICOS',
    price: 280.0,
    storage: 8,
    image_url: 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=400&fit=crop',
    status: true,
  },
  {
    id: 6,
    name: 'SSD NVMe 1TB',
    description: 'Leitura 3500MB/s, escrita 3000MB/s, M.2.',
    category: 'HARDWARE',
    price: 450.0,
    storage: 25,
    image_url: 'https://images.unsplash.com/photo-1531492746076-161ca9bcad58?w=400&h=400&fit=crop',
    status: true,
  },
]);
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        title="Catálogo de Produtos"
        description="Gerencie seu catálogo de produtos e fornecedores."
      />

      <div class="flex gap-5">
        <BaseTab2 :options="TAB_OPTIONS" v-model="activeTab" />
        <BaseButton variant="primary" size="md" type="button" class="flex gap-1" @click="openModal">
          <Plus :size="20" />
          {{ activeTab === 'product' ? 'Adicionar Produto' : 'Adicionar Fornecedor' }}
        </BaseButton>
      </div>
    </div>

    <div class="flex gap-5 justify-between p-4 bg-white rounded-2xl">
      <BaseSearchInput
        class="md:max-w-2/3 lg:max-w-1/2"
        v-model="searchTerm"
        placeholder="Buscar produto por nome ou código..."
      />
      <BaseFilter :filter-config="FILTER_CONFIG" v-model="selectedFilter" />
    </div>

    <!-- Products Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :name="product.name"
        :description="product.description"
        :category="product.category"
        :price="product.price"
        :storage="product.storage"
        :image_url="product.image_url"
        :status="product.status"
      />
    </div>

    <ProductModal />
  </div>
</template>
