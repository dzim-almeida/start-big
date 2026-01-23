<script setup lang="ts">
/**
 * ===========================================================================
 * ARQUIVO: ClientesView.vue
 * MODULO: Clientes
 * DESCRICAO: Pagina principal do modulo de clientes.
 * ===========================================================================
 */

import { ref, computed } from 'vue';
import { UserPlus } from 'lucide-vue-next';

import { ClientStats, ClientTable } from '../components/listagem';
import ClientFormModal from '../components/cadastro/ClientFormModal.vue';
import { useClientes } from '../composables';
import { useClienteActions } from '@/shared/composables/cliente/useClienteActions';
import type { Cliente, FilterTipo } from '../types/clientes.types';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
// ===========================================================================
// COMPOSABLES
// ===========================================================================

const {
  clientes,
  stats,
  activeFilterTipo,
  activeFilterStatus,
  searchQuery,
  isLoading,
  setFilterTipo,
  setFilterStatus,
  setSearch,
  currentPage,
  totalPages,
  totalItems,
  setPage
} = useClientes();

const { toggleAtivoMutation } = useClienteActions();

// ===========================================================================
// ESTADOS DO MODAL
// ===========================================================================

const showModal = ref(false);
const clienteParaEditar = ref<Cliente | null>(null);

// ===========================================================================
// COMPUTED
// ===========================================================================

const filterLabels: Record<FilterTipo, string> = {
  todos: 'Todos os Clientes',
  PF: 'Clientes Pessoa Fisica',
  PJ: 'Clientes Pessoa Juridica',
};

const headerTitle = computed(() => {
  if (searchQuery.value) {
    return `Resultados para: "${searchQuery.value}"`;
  }
  return filterLabels[activeFilterTipo.value];
});

// ===========================================================================
// HANDLERS
// ===========================================================================

function openNewClientModal() {
  clienteParaEditar.value = null;
  showModal.value = true;
}

function openEditClientModal(cliente: Cliente) {
  clienteParaEditar.value = cliente;
  showModal.value = true;
}

function closeModal() {
  showModal.value = false;
  clienteParaEditar.value = null;
}

function handleToggleStatus(cliente: Cliente) {
  toggleAtivoMutation.mutate(cliente.id);
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Header com Filtro Selecionado e Botao Novo Cliente -->
    <div class="flex items-center justify-between">
      <!-- Texto do Filtro Selecionado -->
      <h2 class="text-lg md:text-xl font-bold text-zinc-800">
        {{ headerTitle }}
      </h2>

      <!-- Botao Novo Cliente -->
      <BaseButton @click="openNewClientModal">
        <UserPlus :size="18" />
        Novo Cliente
      </BaseButton>
    </div>

    <!-- Stats Cards -->
    <ClientStats :stats="stats" :loading="isLoading" />

    <!-- Tabela de Clientes (com busca e filtro integrados) -->
    <ClientTable
      :clientes="clientes"
      :is-loading="isLoading"
      :search-query="searchQuery"
      :active-filter="activeFilterTipo"
      :active-filter-status="activeFilterStatus"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      @update:current-page="setPage"
      @edit="openEditClientModal"
      @toggle-status="handleToggleStatus"
      @search="setSearch"
      @filter-change="setFilterTipo"
      @filter-status-change="setFilterStatus"
    />

    <!-- Modal de Cadastro/Edicao -->
    <ClientFormModal :is-open="showModal" :cliente="clienteParaEditar" @close="closeModal" />
  </div>
</template>
