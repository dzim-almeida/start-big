<script setup lang="ts">
import { Plus } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import SalesStatus from './components/SalesStatus.vue';
import SaleTable from './components/SaleTable.vue';
import SaleModal from './components/SaleModal.vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import CustomerSearchModal from './components/CustomerSearchModal.vue';

import { useCustomerSearchModal } from './composables/useCustomerSearchModal';

const { openCustomerModal } = useCustomerSearchModal();
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview title="Vendas" description="Gerencie as vendas do seu estabelecimento." />
      <BaseButton
        variant="primary"
        size="md"
        type="button"
        class="flex gap-1"
        @click="openCustomerModal"
      >
        <Plus :size="20" />
        Nova venda
      </BaseButton>
    </div>

    <SalesStatus />
    <SaleTable />
    
    <CustomerSearchModal />
    <SaleModal />
  </div>
</template>
