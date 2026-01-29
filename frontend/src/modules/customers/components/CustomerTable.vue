<script setup lang="ts">
/**
 * @component CustomerTable
 * @description Customer list table (Presentation Component)
 * Receives prepared data and emits events.
 */

import { ref } from 'vue';
import { Pencil, Power, Mail, Ellipsis } from 'lucide-vue-next';
import type {
  Cliente,
  ClienteFormatted,
  ClienteTableColumn,
  ClienteFilterStatus,
  CustomersStatus,
  CustomersTypes,
} from '../types/clientes.types';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { maskCpfCnpj, maskPhoneNumber } from '@/shared/utils/mask.utils';

// =============================================
// Props & Emits
// =============================================

interface Props {
  customers: ClienteFormatted[];
  isLoading?: boolean;
  currentPage: number;
  totalPages: number;
  totalItems: number;
}

defineProps<Props>();

const searchQuery = defineModel<string>('searchQuery', { default: '' });
const activeFilter = defineModel<CustomersTypes>('activeFilter', { default: null });

const emit = defineEmits<{
  view: [customer: Cliente]
  edit: [customer: Cliente];
  toggleStatus: [customer: Cliente];
  filterStatusChange: [value: ClienteFilterStatus];
  'update:currentPage': [page: number];
}>();

// =============================================
// Configuration
// =============================================

const columns: ClienteTableColumn[] = [
  { key: 'nome', label: 'CLIENTE' },
  { key: 'tipo', label: 'TIPO' },
  { key: 'documento', label: 'CPF / CNPJ' },
  { key: 'contato', label: 'CONTATO' },
  { key: 'status', label: 'STATUS' },
  { key: 'acoes', label: 'AÇÕES RÁPIDAS' },
];

const statusConfig: Record<CustomersStatus, { label: string; class: string; color: string }> = {
  PF: {
    label: 'Pessoa Física',
    class: 'bg-blue-50 text-blue-600 border border-blue-200',
    color: 'bg-blue-500',
  },
  PJ: {
    label: 'Pessoa Jurídica',
    class: 'bg-amber-50 text-amber-600 border border-amber-200',
    color: 'bg-amber-500',
  },
  active: {
    label: 'Ativo',
    class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    color: 'bg-emerald-500',
  },
  inactive: {
    label: 'Desativado',
    class: 'bg-red-50 text-red-600 border border-red-200',
    color: 'bg-red-500',
  },
};

function getCustomerStatus(customer: ClienteFormatted): string {
  return customer.ativo ? 'active' : 'inactive';
}

// =============================================
// Confirm Modal
// =============================================

const confirmModal = {
  isOpen: ref(false),
  data: ref<ClienteFormatted | null>(null),
  open(payload: ClienteFormatted) {
    this.data.value = payload;
    this.isOpen.value = true;
  },
  close() {
    this.isOpen.value = false;
    this.data.value = null;
  },
};

// =============================================
// Handlers
// =============================================

const handleView = (customer: Cliente) => emit('view', customer)

const handleEdit = (customer: Cliente) => emit('edit', customer);

const handleToggleStatus = (customer: ClienteFormatted) => {
  confirmModal.open(customer);
};

const onConfirm = () => {
  if (confirmModal.data.value) {
    emit('toggleStatus', confirmModal.data.value);
    confirmModal.close();
  }
};
</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-empty="customers.length === 0"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    item-label="cliente"
    empty-title="Nenhum cliente encontrado"
    @update:current-page="emit('update:currentPage', $event)"
  >
    <!-- Toolbar Template -->
    <template #toolbar>
      <BaseSearchInput v-model="searchQuery" placeholder="Buscar por nome, email ou CPF..." />
      <BaseFilter v-model="activeFilter" :filterConfig="statusConfig" />
    </template>

    <!-- Table Content (Default Slot) -->
    <table class="w-full text-left min-w-200">
      <thead>
        <tr
          class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
        >
          <th v-for="col in columns" :key="col.key" class="px-4 md:px-6 py-3 md:py-4" :class="col.key === 'acoes' ? 'text-right' : ''">
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-zinc-100">
        <tr
          v-for="customer in customers"
          :key="customer.id"
          class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
          @click="handleView(customer)"
        >
          <!-- Customer (Name + Avatar) -->
          <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors">
            <div class="flex items-center gap-2 text-xs md:text-sm font-semibold">
              <div
                class="w-8 h-8 md:w-10 md:h-10 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center text-[12px] md:text-[13px] font-bold"
              >
                {{ customer.initial }}
              </div>
              <div class="flex flex-col">
                <span class="truncate max-w-30 md:max-w-none">{{ customer.displayName }}</span>
                <div class="flex items-center gap-1 text-[10px] text-zinc-400">
                  <Mail :size="10" />
                  <p>{{ customer.email || 'Sem email' }}</p>
                </div>
              </div>
            </div>
          </td>

          <!-- Type -->
          <td class="px-4 md:px-6 py-3 md:py-4">
            <span
              :class="[
                'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                statusConfig[customer.tipo as CustomersStatus].class,
              ]"
            >
              {{ statusConfig[customer.tipo as CustomersStatus].label }}
            </span>
          </td>

          <!-- Document -->
          <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors">
            {{ maskCpfCnpj(customer.displayDoc) }}
          </td>

          <!-- Contact -->
          <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors">
            {{ maskPhoneNumber(customer.displayPhone) }}
          </td>

          <!-- Status -->
          <td class="px-4 md:px-6 py-3 md:py-4">
            <span
              :class="[
                'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                statusConfig[getCustomerStatus(customer) as CustomersStatus].class,
              ]"
            >
              {{ statusConfig[getCustomerStatus(customer) as CustomersStatus].label }}
            </span>
          </td>

          <!-- Actions -->
          <td class="px-4 md:px-6 py-3 md:py-4">
            <div class="flex items-center justify-end h-full">
              <div class="hidden group-hover:flex items-center justify-end gap-2">
                <!-- Edit Button -->
                <button
                  type="button"
                  class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
                  title="Editar cliente"
                  @click="handleEdit(customer)"
                >
                  <Pencil :size="18" />
                </button>

                <!-- Toggle Status Button -->
                <button
                  type="button"
                  :class="[
                    'p-2 rounded-lg transition-colors cursor-pointer',
                    customer.ativo
                      ? 'text-zinc-400 hover:text-red-500 hover:bg-red-50'
                      : 'text-zinc-400 hover:text-emerald-500 hover:bg-emerald-50',
                  ]"
                  :title="customer.ativo ? 'Desativar cliente' : 'Ativar cliente'"
                  @click="handleToggleStatus(customer)"
                >
                  <Power :size="18" />
                </button>
              </div>
              <div class="p-2 text-zinc-400 group-hover:hidden cursor-pointer">
                <Ellipsis :size="20" />
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Confirm Modal -->
    <BaseConfirmModal
      :is-open="confirmModal.isOpen.value"
      :title="confirmModal.data.value?.ativo ? 'Desativar Cliente?' : 'Ativar Cliente?'"
      confirm-label="Confirmar"
      cancel-label="Cancelar"
      @close="confirmModal.close()"
      @confirm="onConfirm"
    >
      <template #description>
        <p>
          Deseja realmente alterar o status de <br />
          <span class="font-semibold text-zinc-800">
            {{
              (confirmModal.data.value as any)?.nome ||
              (confirmModal.data.value as any)?.nome_fantasia
            }}
          </span>
          ?
        </p>
      </template>
    </BaseConfirmModal>
  </BaseTableContainer>
</template>
