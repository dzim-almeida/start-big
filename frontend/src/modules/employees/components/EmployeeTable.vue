<script setup lang="ts">
/**
 * @component EmployeeTable
 * @description Employee list table with search, filter, and actions
 */

import { ref, computed } from 'vue';
import {
  Ellipsis,
  Funnel,
  Mail,
  Eye,
  Pencil,
  Power,
  Check,
  AlertCircle,
} from 'lucide-vue-next';

import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import type { FuncionarioRead, EmployeeStatus } from '../types/employees.types';
import { useEmployeeModal } from '../composables/useEmployeeModal';
import { useToggleEmployeeActiveMutation } from '../composables/useEmployeesQuery';

// =============================================
// Props & Emits
// =============================================

interface Props {
  employees: FuncionarioRead[];
  isLoading?: boolean;
  isError?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  isError: false,
});

const search = defineModel<string>('search', { default: '' });

// =============================================
// Modal & Mutations
// =============================================

const { openViewModal, openEditModal } = useEmployeeModal();
const toggleActiveMutation = useToggleEmployeeActiveMutation();

// =============================================
// Status Configuration
// =============================================

const statusConfig: Record<EmployeeStatus, { label: string; class: string }> = {
  active: {
    label: 'Ativo',
    class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
  },
  vacation: {
    label: 'Ferias',
    class: 'bg-amber-50 text-amber-600 border border-amber-200',
  },
  inactive: {
    label: 'Desativado',
    class: 'bg-red-50 text-red-600 border border-red-200',
  },
};

// =============================================
// Local State
// =============================================

const selectedStatus = ref<EmployeeStatus | null>(null);
const isFilterMenuOpen = ref(false);

// =============================================
// Computed
// =============================================

/**
 * Maps FuncionarioRead to status for display
 */
function getEmployeeStatus(employee: FuncionarioRead): EmployeeStatus {
  // Map ativo to status (vacation would need backend support)
  return employee.ativo ? 'active' : 'inactive';
}

/**
 * Filters employees based on search and status
 */
const filteredEmployees = computed(() => {
  if (!props.employees) return [];

  return props.employees.filter((employee) => {
    // Text search (name or email)
    const searchLower = search.value.toLowerCase();
    const matchesSearch =
      employee.nome.toLowerCase().includes(searchLower) ||
      (employee.email?.toLowerCase().includes(searchLower) ?? false) ||
      employee.cpf.includes(searchLower);

    // Status filter
    const status = getEmployeeStatus(employee);
    const matchesStatus = selectedStatus.value
      ? status === selectedStatus.value
      : true;

    return matchesSearch && matchesStatus;
  });
});

// =============================================
// Helpers
// =============================================

function getInitials(name: string): string {
  const parts = name.split(' ').filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return `${parts[0].charAt(0)}${parts[parts.length - 1].charAt(0)}`.toUpperCase();
}

function getEmployeeRole(employee: FuncionarioRead): string {
  // Would need cargo data from backend - for now use tipo_contrato or default
  return employee.tipo_contrato || 'Funcionario';
}

// =============================================
// Handlers
// =============================================

function toggleFilterMenu() {
  isFilterMenuOpen.value = !isFilterMenuOpen.value;
}

function selectFilter(statusKey: EmployeeStatus | null) {
  selectedStatus.value = statusKey;
  isFilterMenuOpen.value = false;
}

function handleView(employee: FuncionarioRead) {
  openViewModal(employee);
}

function handleEdit(employee: FuncionarioRead) {
  openEditModal(employee);
}

function handleToggleActive(employee: FuncionarioRead) {
  toggleActiveMutation.mutate(employee.id);
}
</script>

<template>
  <div
    class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-visible"
  >
    <!-- Header with Search and Filter -->
    <div
      class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-5 relative"
    >
      <BaseSearchInput
        v-model="search"
        class="md:max-w-2/3 lg:max-w-1/2"
        placeholder="Buscar por nome, email ou CPF..."
      />

      <div class="relative">
        <button
          @click="toggleFilterMenu"
          :class="[
            'flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs md:text-sm font-semibold border transition-all cursor-pointer select-none',
            selectedStatus
              ? 'bg-brand-primary/10 text-brand-primary border-brand-primary'
              : 'text-zinc-600 border-brand-grey hover:text-brand-primary/80 hover:border-brand-primary/80',
          ]"
        >
          <Funnel :size="20" />
          Filtros
          <span
            v-if="selectedStatus"
            class="ml-1 w-2 h-2 rounded-full bg-brand-primary"
          ></span>
        </button>

        <!-- Filter Dropdown -->
        <div
          v-if="isFilterMenuOpen"
          class="absolute top-full right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-zinc-100 z-50 p-2"
        >
          <div
            class="text-[10px] uppercase font-bold text-zinc-400 px-2 py-2"
          >
            Filtrar por Status
          </div>

          <button
            @click="selectFilter(null)"
            class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            Todos
            <Check
              v-if="selectedStatus === null"
              :size="16"
              class="text-brand-primary"
            />
          </button>

          <button
            v-for="(config, key) in statusConfig"
            :key="key"
            @click="selectFilter(key as EmployeeStatus)"
            class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'w-2 h-2 rounded-full',
                  key === 'active'
                    ? 'bg-emerald-500'
                    : key === 'vacation'
                      ? 'bg-amber-500'
                      : 'bg-red-500',
                ]"
              ></span>
              {{ config.label }}
            </div>
            <Check
              v-if="selectedStatus === key"
              :size="16"
              class="text-brand-primary"
            />
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="p-8">
      <div class="space-y-4">
        <div
          v-for="i in 5"
          :key="i"
          class="flex items-center gap-4 animate-pulse"
        >
          <div class="w-10 h-10 bg-zinc-200 rounded-full"></div>
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-zinc-200 rounded w-1/3"></div>
            <div class="h-3 bg-zinc-100 rounded w-1/4"></div>
          </div>
          <div class="h-6 bg-zinc-200 rounded-full w-16"></div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="isError"
      class="p-8 text-center text-red-500 flex flex-col items-center gap-2"
    >
      <AlertCircle :size="32" />
      <p class="text-sm">Erro ao carregar funcionarios.</p>
      <p class="text-xs text-zinc-400">Verifique sua conexao e tente novamente.</p>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-left min-w-125">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">Funcionario</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Cargo</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-40">
              Acoes Rapidas
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="employee in filteredEmployees"
            :key="employee.id"
            class="hover:bg-zinc-50/50 transition-colors group"
          >
            <!-- Employee Info -->
            <td
              class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors"
            >
              <div
                class="flex items-center gap-4 text-xs md:text-sm font-semibold"
              >
                <div
                  class="w-8 h-8 md:w-10 md:h-10 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center text-[12px] md:text-[13px] font-bold"
                >
                  {{ getInitials(employee.nome) }}
                </div>
                <div class="flex flex-col">
                  <span class="truncate max-w-30 md:max-w-none">{{
                    employee.nome
                  }}</span>
                  <div
                    class="flex items-center gap-1 text-[10px] text-zinc-400"
                  >
                    <Mail :size="10" />
                    <p>{{ employee.email || 'Sem email' }}</p>
                  </div>
                </div>
              </div>
            </td>

            <!-- Role -->
            <td
              class="px-4 md:px-6 py-3 md:py-4 font-medium text-zinc-600 group-hover:text-brand-primary"
            >
              {{ getEmployeeRole(employee) }}
            </td>

            <!-- Status -->
            <td
              class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-bold text-zinc-900"
            >
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap',
                  statusConfig[getEmployeeStatus(employee)].class,
                ]"
              >
                {{ statusConfig[getEmployeeStatus(employee)].label }}
              </span>
            </td>

            <!-- Actions -->
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end h-full">
                <div
                  class="hidden group-hover:flex items-center justify-end gap-1 transition-all duration-200"
                >
                  <button
                    title="Visualizar Detalhes"
                    class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors cursor-pointer"
                    @click="handleView(employee)"
                  >
                    <Eye :size="18" />
                  </button>
                  <button
                    title="Editar"
                    class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors cursor-pointer"
                    @click="handleEdit(employee)"
                  >
                    <Pencil :size="18" />
                  </button>
                  <button
                    :title="employee.ativo ? 'Desativar' : 'Ativar'"
                    :class="[
                      'p-2 rounded-lg transition-colors cursor-pointer',
                      employee.ativo
                        ? 'text-zinc-400 hover:text-red-600 hover:bg-red-50'
                        : 'text-zinc-400 hover:text-emerald-600 hover:bg-emerald-50',
                    ]"
                    @click="handleToggleActive(employee)"
                  >
                    <Power :size="18" />
                  </button>
                </div>
                <div
                  class="p-2 text-zinc-400 group-hover:hidden cursor-pointer"
                >
                  <Ellipsis :size="20" />
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div
      v-if="!isLoading && !isError && filteredEmployees.length === 0"
      class="p-8 text-center text-zinc-400 text-sm"
    >
      <span v-if="employees.length > 0"
        >Nenhum funcionario encontrado com estes filtros.</span
      >
      <span v-else>Nenhum funcionario cadastrado.</span>
    </div>

    <!-- Footer with Pagination -->
    <div
      v-if="!isLoading && !isError && filteredEmployees.length > 0"
      class="px-6 py-5 border-t border-zinc-100 bg-white flex flex-col md:flex-row items-center justify-between gap-4 mt-auto"
    >
      <span class="text-xs text-zinc-500 font-bold uppercase tracking-widest">
        {{ filteredEmployees.length }} Registros
      </span>

      <div class="flex items-center gap-2">
        <button
          class="h-9 px-4 rounded-lg text-xs font-bold text-zinc-400 bg-zinc-50 cursor-not-allowed transition-colors"
          disabled
        >
          Anterior
        </button>
        <button
          class="h-9 w-9 rounded-lg bg-brand-primary text-white text-xs font-bold shadow-sm shadow-brand-primary/20 hover:bg-brand-primary/90 transition-all cursor-pointer"
        >
          1
        </button>
        <button
          class="h-9 px-4 rounded-lg text-xs font-bold text-zinc-700 bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 transition-all shadow-sm cursor-pointer"
        >
          Proximo
        </button>
      </div>
    </div>
  </div>
</template>
