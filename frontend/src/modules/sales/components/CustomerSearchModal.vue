<script setup lang="ts">
import { computed } from 'vue';
import {
  UserCircle2,
  Building2,
  Plus,
  UserRoundX
 } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useCustomerSearchModal } from '../composables/flows/useCustomerSearchModal';

import { getInitials } from '@/shared/utils/string.utils';

const {
  searchTerm,
  isSearchingCustomers,
  customers,
  customerModalIsOpen,
  modalMode,
  closeCustomerModal,
  openCreateCustomerModal,
  selectCustomer,
} = useCustomerSearchModal();

const isChangeMode = computed(() => modalMode.value === 'change');
</script>

<template>
  <BaseModal
    :is-open="customerModalIsOpen"
    :title="isChangeMode ? 'Trocar Cliente' : 'Selecionar Cliente'"
    :subtitle="isChangeMode ? 'Escolha um cliente para esta venda' : 'Escolha ou cadastre um cliente para esta venda'"
    size="md"
    :overlay="isChangeMode"
    @close="closeCustomerModal"
  >
    <BaseSearchInput v-model="searchTerm" placeholder="Buscar por nome ou CPF/CNPJ" />

    <div class="mt-3 max-h-80 overflow-y-auto divide-y divide-zinc-100 -mx-1 px-1">
      <!-- Skeleton de loading -->
      <template v-if="isSearchingCustomers">
        <div v-for="n in 5" :key="n" class="flex items-center gap-3 px-2 py-3 animate-pulse">
          <div class="w-9 h-9 rounded-full bg-zinc-200 shrink-0" />
          <div class="flex-1 space-y-1.5">
            <div class="h-3 w-1/2 bg-zinc-200 rounded" />
            <div class="h-2.5 w-1/3 bg-zinc-100 rounded" />
          </div>
        </div>
      </template>

      <!-- Lista de clientes -->
      <template v-else-if="customers?.length! > 0">
        <button
          v-for="customer in customers"
          :key="customer.id"
          type="button"
          :class="[
            'w-full flex items-center gap-3 px-2 py-3 rounded-xl text-left transition-colors hover:bg-zinc-50 cursor-pointer',
          ]"
          @click="selectCustomer(customer.id)"
        >
          <div
            class="w-9 h-9 rounded-full bg-brand-primary/10 flex items-center justify-center shrink-0"
          >
            <span class="text-[11px] font-bold text-brand-primary">
              {{ getInitials(customer.tipo == 'PF' ? customer.nome : customer.razao_social) }}
            </span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-900 truncate">
              {{ customer.tipo == 'PF' ? customer.nome : customer.razao_social }}
            </p>
            <p class="text-[11px] text-zinc-400 truncate">
              {{ customer.tipo == 'PF' ? customer.cpf : customer.cnpj }}
              <template v-if="customer.telefone"> · {{ customer.telefone }} </template>
            </p>
          </div>
          <component
            :is="customer.tipo === 'PF' ? UserCircle2 : Building2"
            :size="15"
            class="text-zinc-300 shrink-0 mr-1"
          />
        </button>
      </template>

      <!-- Estado vazio -->
      <div v-else class="py-10 text-center text-zinc-400">
        <p class="text-sm font-medium">Nenhum cliente encontrado</p>
        <p class="text-xs mt-1">
          {{
            searchTerm
              ? 'Tente outro termo ou cadastre um novo cliente.'
              : 'Cadastre o primeiro cliente abaixo.'
          }}
        </p>
      </div>
    </div>

    <template #footer>
      <div class="flex flex-col gap-2">
        <BaseButton variant="primary" class="w-full" @click="openCreateCustomerModal">
          <Plus :size="16" class="mr-1.5" />
          Cadastrar novo cliente
        </BaseButton>
        <BaseButton variant="secondary" class="w-full" @click="selectCustomer(null)">
          <UserRoundX :size="16" class="mr-1.5" />
          {{ isChangeMode ? 'Remover cliente' : 'Venda sem cliente' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
