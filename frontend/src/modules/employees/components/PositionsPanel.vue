<script setup lang="ts">
/**
 * @component PositionsPanel
 * @description List and search cargos with summary and cards
 */

import { computed, ref } from 'vue';
import { AlertCircle, BriefcaseBusiness, ShieldCheck, Users } from 'lucide-vue-next';

import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import PositionCard from './PositionCard.vue';

import type { CargoRead } from '../types/positions.types';
import type { FuncionarioRead } from '../types/employees.types';
import {
  POSITION_LEVEL_FILTERS,
  getAccessLevel,
  getPermissionStats,
} from '../constants/positions.constants';

interface Props {
  positions: CargoRead[];
  employees: FuncionarioRead[];
  isLoading?: boolean;
  isError?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  positions: () => [],
  employees: () => [],
  isLoading: false,
  isError: false,
});

const emit = defineEmits<{
  (e: 'view', position: CargoRead): void;
  (e: 'edit', position: CargoRead): void;
  (e: 'remove', position: CargoRead): void;
}>();

const search = defineModel<string>('search', { default: '' });
const selectedLevel = ref<string | null>(null);

const positionsList = computed(() => props.positions || []);

const employeesByCargo = computed(() => {
  const map = new Map<number, number>();
  props.employees.forEach((employee) => {
    if (!employee.cargo_id) return;
    map.set(employee.cargo_id, (map.get(employee.cargo_id) || 0) + 1);
  });
  return map;
});

const assignedEmployees = computed(() => {
  return props.employees.filter((employee) => employee.cargo_id).length;
});

const positionsWithMeta = computed(() => {
  return positionsList.value.map((position) => {
    const permissions = getPermissionStats(position.permissoes);
    const accessLevel = getAccessLevel(position.permissoes);
    const employees = employeesByCargo.value.get(position.id) || 0;

    return {
      position,
      permissions,
      accessLevel,
      employees,
    };
  });
});

const filteredPositions = computed(() => {
  const term = search.value.trim().toLowerCase();
  const level = selectedLevel.value;
  let list = positionsWithMeta.value;

  if (term) {
    list = list.filter((item) =>
      item.position.nome.toLowerCase().includes(term),
    );
  }

  if (level) {
    list = list.filter((item) => item.accessLevel.id === level);
  }

  return [...list].sort((a, b) =>
    a.position.nome.localeCompare(b.position.nome),
  );
});

const averagePermissionCoverage = computed(() => {
  if (!positionsWithMeta.value.length) return 0;
  const total = positionsWithMeta.value.reduce(
    (acc, item) => acc + item.permissions.ratio,
    0,
  );
  return Math.round((total / positionsWithMeta.value.length) * 100);
});

const statsCards = computed(() => [
  {
    key: 'positions',
    icon: BriefcaseBusiness,
    label: 'Cargos ativos',
    value: String(positionsList.value.length),
  },
  {
    key: 'assigned',
    icon: Users,
    label: 'Colaboradores vinculados',
    value: String(assignedEmployees.value),
  },
  {
    key: 'coverage',
    icon: ShieldCheck,
    label: 'Cobertura media',
    value: `${averagePermissionCoverage.value}%`,
  },
]);

function handleView(position: CargoRead) {
  emit('view', position);
}

function handleEdit(position: CargoRead) {
  emit('edit', position);
}

function handleRemove(position: CargoRead) {
  emit('remove', position);
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <BaseStatsCard
        v-for="card in statsCards"
        :key="card.key"
        :icon="card.icon"
        :label="card.label"
        :value="card.value"
      />
    </div>

    <div class="flex gap-4 rounded-2xl border border-zinc-200 bg-white p-4">
      <BaseSearchInput
        v-model="search"
        placeholder="Buscar cargo..."
        class="md:max-w-2/3 lg:max-w-1/2"
      />
      <BaseFilter
        v-model="selectedLevel"
        :filter-config="POSITION_LEVEL_FILTERS"
        title="Filtrar por nivel"
        button-label="Filtros"
      />
    </div>

    <div v-if="isLoading" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div
        v-for="i in 6"
        :key="i"
        class="h-24 rounded-2xl border border-zinc-100 bg-white p-4 shadow-sm"
      >
        <div class="flex items-center gap-4 animate-pulse">
          <div class="h-12 w-12 rounded-2xl bg-zinc-100"></div>
          <div class="flex-1 space-y-2">
            <div class="h-3 w-1/2 rounded bg-zinc-100"></div>
            <div class="h-2 w-1/3 rounded bg-zinc-100"></div>
            <div class="h-2 w-2/3 rounded bg-zinc-100"></div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-else-if="isError"
      class="flex flex-col items-center gap-2 rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-red-500"
    >
      <AlertCircle :size="32" />
      <p class="text-sm font-semibold">Erro ao carregar cargos.</p>
      <p class="text-xs text-red-400">Tente novamente em alguns instantes.</p>
    </div>

    <div
      v-else
      class="grid grid-cols-1 gap-4 lg:grid-cols-2"
    >
      <PositionCard
        v-for="(item, index) in filteredPositions"
        :key="item.position.id"
        :id="item.position.id"
        :name="item.position.nome"
        :employees="item.employees"
        :permissions-enabled="item.permissions.enabled"
        :permissions-total="item.permissions.total"
        :theme-index="index"
        @view="handleView(item.position)"
        @edit="handleEdit(item.position)"
        @remove="handleRemove(item.position)"
      />
    </div>

    <div
      v-if="!isLoading && !isError && filteredPositions.length === 0"
      class="rounded-2xl border border-dashed border-zinc-200 bg-white p-10 text-center text-sm text-zinc-400"
    >
      Nenhum cargo encontrado. Ajuste a busca ou cadastre um novo cargo.
    </div>
  </div>
</template>
