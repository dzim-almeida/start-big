<script setup lang="ts">
/**
 * @component EmployeeTable
 * @description Employee list table with search, filter, and actions
 */

import { ref, computed, watch } from 'vue';
import {
  Ellipsis,
  Mail,
  Pencil,
  Power,
} from 'lucide-vue-next';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { getInitials } from '@/shared/utils/string.utils';

import type { FuncionarioRead, EmployeeStatus } from '../types/employees.types';
import type { CargoRead } from '../types/positions.types';
import { useEmployeeModal } from '../composables/useEmployeeModal';
import { useToggleEmployeeActiveMutation } from '../composables/useEmployeesQuery';

// =============================================
// Props & Emits
// =============================================

interface Props {
  employees: FuncionarioRead[];
  isLoading?: boolean;
  isError?: boolean;
  positions?: CargoRead[];
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  isError: false,
  positions: () => [],
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

const statusConfig: Record<EmployeeStatus, { label: string; class: string, color: string }> = {
  active: {
    label: 'Ativo',
    class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    color: 'bg-emerald-500'
  },
  vacation: {
    label: 'Ferias',
    class: 'bg-amber-50 text-amber-600 border border-amber-200',
    color: 'bg-amber-500'
  },
  inactive: {
    label: 'Desativado',
    class: 'bg-red-50 text-red-600 border border-red-200',
    color: 'bg-red-500'
  },
};

// =============================================
// Local State
// =============================================

const ITEMS_PER_PAGE = 10;
const currentPage = ref(1);
const selectedStatus = ref<EmployeeStatus | null>(null);

watch([search, selectedStatus], () => { currentPage.value = 1; });

const positionsById = computed(() => {
  return new Map((props.positions || []).map((position) => [position.id, position]));
});

// =============================================
// Computed
// =============================================

/**
 * Maps FuncionarioRead to status for display
 */
function getEmployeeStatus(employee: FuncionarioRead): EmployeeStatus {
  return employee.ativo ? 'active' : 'inactive';
}

const filteredEmployees = computed(() => {
  if (!props.employees) return [];

  return props.employees.filter((employee) => {
    const searchLower = search.value.toLowerCase();
    const matchesSearch =
      employee.nome.toLowerCase().includes(searchLower) ||
      (employee.email?.toLowerCase().includes(searchLower) ?? false) ||
      employee.cpf.includes(searchLower);

    const status = getEmployeeStatus(employee);
    const matchesStatus = selectedStatus.value
      ? status === selectedStatus.value
      : true;

    return matchesSearch && matchesStatus;
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredEmployees.value.length / ITEMS_PER_PAGE)));

const pagedEmployees = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE;
  return filteredEmployees.value.slice(start, start + ITEMS_PER_PAGE);
});

function getEmployeeRole(employee: FuncionarioRead): string {
  if (employee.cargo_id) {
    const cargo = positionsById.value.get(employee.cargo_id);
    if (cargo?.nome) return cargo.nome;
  }
  return employee.tipo_contrato || 'Funcionario';
}

// =============================================
// Handlers
// =============================================

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
  <BaseTableContainer
    :is-loading="isLoading"
    :is-error="isError"
    :is-empty="filteredEmployees.length === 0"
    :total-items="filteredEmployees.length"
    :current-page="currentPage"
    :total-pages="totalPages"
    item-label="funcionário"
    empty-title="Nenhum funcionário encontrado"
    :empty-description="employees.length > 0 ? 'Tente ajustar os filtros de busca.' : 'Cadastre seu primeiro funcionário.'"
    error-title="Erro ao carregar funcionários"
    error-description="Verifique sua conexão e tente novamente."
    @update:current-page="currentPage = $event"
  >
    <!-- Toolbar -->
    <template #toolbar>
      <BaseSearchInput
        v-model="search"
        placeholder="Buscar por nome, email ou CPF..."
      />

      <BaseFilter
        v-model="selectedStatus"
        :filterConfig="statusConfig"
      />
    </template>

    <!-- Table Content -->
    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-125">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">Funcionário</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Cargo</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-40">
              Ações Rapidas
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="employee in pagedEmployees"
            :key="employee.id"
            class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
            @click="handleView(employee)"
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
                    title="Editar"
                    class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors cursor-pointer"
                    @click.stop="handleEdit(employee)"
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
                    @click.stop="handleToggleActive(employee)"
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
  </BaseTableContainer>
</template>
