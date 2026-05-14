<script setup lang="ts">
import { computed } from 'vue';
import { X } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import ProductSearch from './SaleModal/ProductSearch.vue';
import CustomerCard from './SaleModal/CustomerCard.vue';
import SaleCard from './SaleModal/SaleCard.vue';
import SaleItemsTable from './SaleModal/SaleItemsTable.vue';
import SaleSummary from './SaleModal/SaleSummary.vue';

import { SALE_FILTERS, STATUS_COLORS } from '../constants';

import { useSaleModal } from '../composables/useSaleModal';


const { saleModalIsOpen, closeSaleModal, sale, selectedSaleId, isEditMode, isViewMode } = useSaleModal();

const saleNumberDisplay = computed(() => {
  if (!sale.value) return '...';

  let base = 'Venda #';
  const idLength = sale.value?.id.toString().length;
  if (idLength) {
    const zerosToAdd = 6 - idLength;
    base += '0'.repeat(zerosToAdd);
  }

  return base + sale.value.id;
});
</script>

<template>
  <BaseModal
    :is-open="saleModalIsOpen"
    :title="saleNumberDisplay"
    subtitle="Gerencie os detalhes desta venda, adicione produtos, finalize ou cancele a venda"
    size="4xl"
    @close="closeSaleModal"
  >
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-zinc-800">
            {{ saleNumberDisplay }}
          </h2>
          <span
            :class="[
              'px-2 py-0.5 text-xs font-medium rounded-full',
              STATUS_COLORS[sale?.status!].text,
              STATUS_COLORS[sale?.status!].bg,
            ]"
          >
            {{ SALE_FILTERS[sale?.status!].label }}
          </span>
        </div>

        <button
          type="button"
          class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          @click="closeSaleModal()"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <main class="w-full min-h-[80vh] flex flex-wrap md:flex-nowrap gap-4 border-red-500">
      <section class="w-full md:w-2/3 flex flex-col gap-5">
        <ProductSearch v-if="isEditMode" :sale-id="selectedSaleId"/>
        <SaleItemsTable :sale="sale" :readonly="isViewMode"/>
        <SaleSummary :subtotal="sale?.subtotal"  :discount="sale?.descontos" :delivery="sale?.entrega" :total="sale?.total"/>
      </section>
      <section class="w-full md:w-1/3 flex flex-col gap-4">
        <CustomerCard :customer="sale?.cliente" />
        <SaleCard :sale="sale" :readonly="isViewMode" />
        <div class="mt-auto flex justify-around gap-5 w-full">
          <BaseButton variant="secondary" size="md" class="flex-1" @click="closeSaleModal()">
            Cancelar
          </BaseButton>
          <BaseButton variant="primary" size="md" class="flex-1">
            Finalizar
          </BaseButton>
        </div>
      </section>
    </main>
  </BaseModal>
</template>
