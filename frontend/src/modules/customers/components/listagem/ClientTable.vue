<script setup lang="ts">
/**
 * ===========================================================================
 * ARQUIVO: ClientTable.vue
 * MODULO: Clientes
 * DESCRICAO: Tabela de listagem de clientes (Componente de Apresentacao)
 *            Recebe dados prontos e emite eventos.
 * ===========================================================================
 */

import { ref } from 'vue';
import { Pencil, Power, Search, Filter } from 'lucide-vue-next';
import type { Cliente, ClienteFormatted, ClienteTableColumn, FilterTipo, ClienteFilterStatus } from '../../types/clientes.types';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';

// ===========================================================================
// PROPS E EMITS
// ===========================================================================

interface Props {
  clientes: ClienteFormatted[]; // Agora recebe a lista PRONTA e ja formatada
  isLoading?: boolean;
  searchQuery: string;
  activeFilter: FilterTipo;
  activeFilterStatus: ClienteFilterStatus;
  
  // Props de Paginacao
  currentPage: number;
  totalPages: number;
  totalItems: number;
}

defineProps<Props>();

const emit = defineEmits<{
  edit: [cliente: Cliente];
  toggleStatus: [cliente: Cliente];
  search: [value: string];
  filterChange: [value: FilterTipo];
  filterStatusChange: [value: ClienteFilterStatus];
  'update:currentPage': [page: number]; // Para v-model da pagina no pai
}>();

// ===========================================================================
// ESTADOS LOCAIS
// ===========================================================================

const isFilterOpen = ref(false);

// ===========================================================================
// CONFIGURACOES
// ===========================================================================

const columns: ClienteTableColumn[] = [
  { key: 'nome', label: 'CLIENTE' },
  { key: 'tipo', label: 'TIPO' },
  { key: 'documento', label: 'CPF / CNPJ' },
  { key: 'contato', label: 'CONTATO' },
  { key: 'status', label: 'STATUS' },
  { key: 'acoes', label: 'AÇÕES' },
];

const filterOptions: { id: FilterTipo; label: string; shortLabel: string }[] = [
  { id: 'todos', label: 'Todos os clientes', shortLabel: 'Todos' },
  { id: 'PF', label: 'Pessoa Fisica (CPF)', shortLabel: 'PF' },
  { id: 'PJ', label: 'Pessoa Juridica (CNPJ)', shortLabel: 'PJ' },
];

const statusFilterOptions: { id: ClienteFilterStatus; label: string }[] = [
  { id: 'ativos', label: 'Apenas Ativos' },
  { id: 'inativos', label: 'Apenas Inativos' },
  { id: 'todos', label: 'Todos os Status' },
];

const statusConfig = {
  true: { label: 'Ativo', class: 'bg-emerald-50 text-emerald-600' },
  false: { label: 'Inativo', class: 'bg-red-50 text-red-600' },
};

const tipoConfig = {
  PF: { label: 'Pessoa Fisica', class: 'bg-blue-50 text-blue-600' },
  PJ: { label: 'Pessoa Juridica', class: 'bg-orange-50 text-orange-600' },
};

// ===========================================================================
// MODAL DE CONFIRMACAO
// ===========================================================================

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

// ...

// ===========================================================================
// HANDLERS
// ===========================================================================

const handleSearch = (e: Event) => {
  const target = e.target as HTMLInputElement;
  emit('search', target.value);
};

const toggleFilterDropdown = () => {
  isFilterOpen.value = !isFilterOpen.value;
};

const closeFilterDropdown = () => {
  // Delay to allow click events to fire first
  setTimeout(() => {
    isFilterOpen.value = false;
  }, 150);
};

const handleFilterSelect = (filter: FilterTipo) => {
  emit('filterChange', filter);
  isFilterOpen.value = false;
};

const handleStatusFilterSelect = (status: ClienteFilterStatus) => {
  emit('filterStatusChange', status);
  isFilterOpen.value = false;
};

const handleEdit = (cliente: Cliente) => emit('edit', cliente);

const handleToggleStatus = (cliente: ClienteFormatted) => {
  confirmModal.open(cliente);
};

// ...

// In template:
// {{ confirmModal.data.value?.displayName }}

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
    :is-empty="clientes.length === 0"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    item-label="cliente"
    empty-title="Nenhum cliente encontrado"
    @update:current-page="emit('update:currentPage', $event)"
  >
    <!-- Template para Toolbar -->
    <template #toolbar>
      <div class="flex items-center gap-3 w-full">
        <!-- Campo de Busca -->
        <div class="relative flex-1 max-w-md">
          <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search :size="16" class="text-zinc-400" />
          </div>
          <input
            type="text"
            :value="searchQuery"
            placeholder="Buscar por nome, email ou CPF..."
            class="w-full pl-11 pr-4 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary transition-all placeholder:text-zinc-400"
            @input="handleSearch"
          />
        </div>

        <!-- Dropdown de Filtro -->
        <div class="relative">
          <button
            type="button"
            class="flex-1 px-4 py-2.5 bg-white border border-zinc-200 rounded-xl text-sm font-medium text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300 transition-colors flex items-center gap-2"
            @click="toggleFilterDropdown"
            @blur="closeFilterDropdown"
          >
            <Filter :size="16" class="text-zinc-400" />
            <span class="hidden md:inline">Filtros</span>
          </button>

          <!-- Dropdown Menu -->
          <div
            v-if="isFilterOpen"
            class="absolute right-0 mt-2 w-52 bg-white border border-zinc-200 rounded-xl shadow-lg z-50 overflow-hidden"
          >
            <!-- Filtro por Tipo -->
            <div class="px-3 py-2 border-b border-zinc-100 bg-zinc-50/50">
              <span class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Tipo de Cliente</span>
            </div>
            <div class="py-1">
              <button
                v-for="option in filterOptions"
                :key="option.id"
                type="button"
                class="w-full px-3 py-2.5 text-left text-sm hover:bg-zinc-50 transition-colors flex items-center justify-between"
                :class="{
                  'text-brand-primary font-medium': activeFilter === option.id,
                  'text-zinc-600': activeFilter !== option.id,
                }"
                @mousedown.prevent="handleFilterSelect(option.id)"
              >
                {{ option.label }}
                <span
                  v-if="activeFilter === option.id"
                  class="w-1.5 h-1.5 rounded-full bg-brand-primary"
                ></span>
              </button>
            </div>

            <!-- Filtro por Status -->
            <div class="px-3 py-2 border-t border-b border-zinc-100 bg-zinc-50/50">
              <span class="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Status</span>
            </div>
            <div class="py-1">
              <button
                v-for="status in statusFilterOptions"
                :key="status.id"
                type="button"
                class="w-full px-3 py-2.5 text-left text-sm hover:bg-zinc-50 transition-colors flex items-center justify-between"
                :class="{
                  'text-brand-primary font-medium': activeFilterStatus === status.id,
                  'text-zinc-600': activeFilterStatus !== status.id,
                }"
                @mousedown.prevent="handleStatusFilterSelect(status.id)"
              >
                {{ status.label }}
                <span
                  v-if="activeFilterStatus === status.id"
                  class="w-1.5 h-1.5 rounded-full bg-brand-primary"
                ></span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Table Content (Default Slot) -->
    <table class="w-full text-left min-w-200">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th v-for="col in columns" :key="col.key" class="px-4 md:px-6 py-3 md:py-4">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="cliente in clientes"
            :key="cliente.id"
            class="hover:bg-zinc-50/50 transition-colors group"
          >
            <!-- Cliente (Nome + Avatar) -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center gap-2 text-xs md:text-sm font-semibold">
                <div
                  class="w-8 h-8 md:w-9 md:h-9 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center text-[11px] md:text-xs font-bold"
                >
                  {{ cliente.initial }}
                </div>
                <div>
                  <span class="block truncate max-w-37.5 md:max-w-none text-zinc-900">
                    {{ cliente.displayName }}
                  </span>
                  <span class="block text-[10px] text-zinc-400">
                    {{ cliente.email || '-' }}
                  </span>
                </div>
              </div>
            </td>

            <!-- Tipo -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  tipoConfig[cliente.tipo].class,
                ]"
              >
                {{ tipoConfig[cliente.tipo].label }}
              </span>
            </td>

            <!-- Documento -->
            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600">
              {{ cliente.displayDoc }}
            </td>

            <!-- Contato -->
            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm text-zinc-600">
              {{ cliente.displayPhone }}
            </td>

            <!-- Status -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  statusConfig[String(cliente.ativo) as 'true' | 'false'].class,
                ]"
              >
                {{ statusConfig[String(cliente.ativo) as 'true' | 'false'].label }}
              </span>
            </td>

            <!-- Acoes -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end gap-2">
                <!-- Botao Editar -->
                <button
                  type="button"
                  class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors"
                  title="Editar cliente"
                  @click="handleEdit(cliente)"
                >
                  <Pencil :size="16" />
                </button>

                <!-- Botao Ativar/Desativar -->
                <button
                  type="button"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    cliente.ativo
                      ? 'text-zinc-400 hover:text-red-500 hover:bg-red-50'
                      : 'text-zinc-400 hover:text-emerald-500 hover:bg-emerald-50',
                  ]"
                  :title="cliente.ativo ? 'Desativar cliente' : 'Ativar cliente'"
                  @click="handleToggleStatus(cliente)"
                >
                  <Power :size="16" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
    </table>

    <!-- Modal de Confirmacao Generic -->
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
