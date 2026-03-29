<script setup lang="ts">
/**
 * @component CustomersView
 * @description Main page for the customers module.
 * Displays customer list with stats, filtering, and CRUD operations.
 */

import { Plus } from 'lucide-vue-next';

import { CARDS_INFO } from '../constants/clientes.constants';

import CustomerTable from '../components/CustomerTable.vue';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';

import { useCustomers } from '../composables/useCustomers';
import { useCustomerModal } from '../composables/modal/useCustomerModal';
import { useToggleCustomerAtivoMutation } from '../composables/request/useCustomerUpdate.mutate';

import type { Cliente } from '../types/clientes.types';

// =============================================
// Composables
// =============================================

const {
  customers,
  stats,
  activeFilterTipo,
  searchQuery,
  isLoading,
  currentPage,
  totalPages,
  totalItems,
  setPage,
} = useCustomers();

const { openCreateModal, openViewModal, openEditModal } = useCustomerModal();
const toggleAtivoMutation = useToggleCustomerAtivoMutation();

// =============================================
// Handlers
// =============================================

function handleView(customer: Cliente) {
  openViewModal(customer);
}

function handleEdit(customer: Cliente) {
  openEditModal(customer);
}

function handleToggleStatus(customer: Cliente) {
  toggleAtivoMutation.mutate(customer.id);
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Header with Filter Title and New Customer Button -->
    <div class="flex items-center justify-between">
      <!-- Filter Title -->
      <PageReview
        title="Clientes Cadastrados"
        description="Gerencie as informacoes dos seus clientes"
      />

      <!-- New Customer Button -->
      <BaseButton @click="openCreateModal">
        <Plus :size="20" class="mr-2" />
        Adicionar Cliente
      </BaseButton>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 md:gap-6">
      <BaseStatsCard
        v-for="item in CARDS_INFO"
        :key="item.key"
        :icon="item.icon"
        :label="item.label"
        :value="String(stats[item.key])"
      />
    </div>

    <!-- Customer Table (with integrated search and filters) -->
    <CustomerTable
      v-model:searchQuery="searchQuery"
      v-model:activeFilter="activeFilterTipo"
      :customers="customers"
      :is-loading="isLoading"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      @update:current-page="setPage"
      @view="handleView"
      @edit="handleEdit"
      @toggle-status="handleToggleStatus"
    />

  </div>
</template>
