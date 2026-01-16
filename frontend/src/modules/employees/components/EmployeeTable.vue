<script setup lang="ts">
import { ref, computed } from 'vue'; // Importar ref e computed
import { 
  Ellipsis, Funnel, Mail, Eye, Pencil, Trash2, Check 
} from 'lucide-vue-next';

import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import type { Employee } from '../types/employees.types';

interface Props {
  employees: Employee[];
}

const props = defineProps<Props>();

// --- 1. CONFIGURAÇÃO E ESTADO ---

const statusConfig = {
  active: {
    label: 'Ativo',
    class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
  },
  vacation: {
    label: 'Férias',
    class: 'bg-amber-50 text-amber-600 border border-amber-200',
  },
  inactive: {
    label: 'Desativado',
    class: 'bg-red-50 text-red-600 border border-red-200',
  },
};

// Variáveis reativas para controle dos filtros
const searchQuery = ref('');
const selectedStatus = ref<string | null>(null); // null significa "todos"
const isFilterMenuOpen = ref(false);

// --- 2. LÓGICA DE FILTRAGEM (COMPUTED) ---

const filteredEmployees = computed(() => {
  if (!props.employees) return [];

  return props.employees.filter((employee) => {
    // Filtro de Texto (Nome ou Email)
    const matchesSearch = 
      employee.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      employee.email.toLowerCase().includes(searchQuery.value.toLowerCase());

    // Filtro de Status
    const matchesStatus = selectedStatus.value 
      ? employee.status === selectedStatus.value 
      : true;

    return matchesSearch && matchesStatus;
  });
});

// Funções auxiliares
function getInitials(name: string): string {
  const initials = name.split(' ').map((value) => value.charAt(0).toUpperCase());
  return `${initials[0]}${initials[1]}`;
}

function toggleFilterMenu() {
  isFilterMenuOpen.value = !isFilterMenuOpen.value;
}

function selectFilter(statusKey: string | null) {
  selectedStatus.value = statusKey;
  isFilterMenuOpen.value = false; // Fecha o menu após selecionar
}
</script>

<template>
  <div class="bg-white rounded-2xl md:rounded-3xl border border-zinc-200 shadow-sm overflow-visible"> 
    <div class="p-4 md:p-6 border-b border-zinc-100 flex items-center gap-5 relative">
      <BaseSearchInput 
        v-model="searchQuery" 
        class="md:max-w-2/3 lg:max-w-1/2" 
        placeholder="Buscar por nome ou email..." 
      />
      
      <div class="relative">
        <button
          @click="toggleFilterMenu"
          :class="[
            'flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs md:text-sm font-semibold border transition-all cursor-pointer select-none',
            selectedStatus 
              ? 'bg-brand-primary/10 text-brand-primary border-brand-primary' 
              : 'text-zinc-600 border-brand-grey hover:text-brand-primary/80 hover:border-brand-primary/80'
          ]"
        >
          <Funnel :size="20" />
          Filtros
          <span v-if="selectedStatus" class="ml-1 w-2 h-2 rounded-full bg-brand-primary"></span>
        </button>

        <div 
          v-if="isFilterMenuOpen"
          class="absolute top-full right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-zinc-100 z-50 p-2"
        >
          <div class="text-[10px] uppercase font-bold text-zinc-400 px-2 py-2">Filtrar por Status</div>
          
          <button
            @click="selectFilter(null)"
            class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            Todos
            <Check v-if="selectedStatus === null" :size="16" class="text-brand-primary"/>
          </button>

          <button
            v-for="(config, key) in statusConfig"
            :key="key"
            @click="selectFilter(key as string)"
            class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            <div class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full', config.class.split(' ')[0].replace('bg-', 'bg-')]"></span>
              {{ config.label }}
            </div>
            <Check v-if="selectedStatus === key" :size="16" class="text-brand-primary"/>
          </button>
        </div>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-125">
        <thead>
          <tr class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100">
            <th class="px-4 md:px-6 py-3 md:py-4">Funcionário</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Cargo</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-40">Ações Rápidas</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="employee in filteredEmployees"
            :key="employee.id"
            class="hover:bg-zinc-50/50 transition-colors group"
          >
            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 group-hover:text-brand-primary transition-colors">
              <div class="flex items-center gap-4 text-xs md:text-sm font-semibold">
                <div class="w-8 h-8 md:w-10 md:h-10 bg-brand-primary/10 text-brand-primary rounded-full flex items-center justify-center text-[12px] md:text-[13px] font-bold">
                  {{ getInitials(employee.name) }}
                </div>
                <div class="flex flex-col">
                  <span class="truncate max-w-30 md:max-w-none">{{ employee.name }}</span>
                  <div class="flex items-center gap-1 text-[10px] text-zinc-400">
                    <Mail :size="10" />
                    <p>{{ employee.email }}</p>
                  </div>
                </div>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4 font-medium text-zinc-600 group-hover:text-brand-primary">
              {{ employee.role }}
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-bold text-zinc-900">
              <span :class="['px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap', statusConfig[employee.status].class]">
                {{ statusConfig[employee.status].label }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
               <div class="flex items-center justify-end h-full">
                <div class="hidden group-hover:flex items-center justify-end gap-1 transition-all duration-200">
                  <button title="Visualizar Detalhes" class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors cursor-pointer">
                    <Eye :size="18" />
                  </button>
                  <button title="Editar" class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 rounded-lg transition-colors cursor-pointer">
                    <Pencil :size="18" />
                  </button>
                  <button title="Excluir" class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer">
                    <Trash2 :size="18" />
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
    </div>

    <div v-if="filteredEmployees.length === 0" class="p-8 text-center text-zinc-400 text-sm">
      <span v-if="employees.length > 0">Nenhum funcionário encontrado com estes filtros.</span>
      <span v-else>Nenhum funcionário cadastrado.</span>
    </div>

    <div
      v-if="filteredEmployees.length > 0"
      class="px-6 py-5 border-t border-zinc-100 bg-white flex flex-col md:flex-row items-center justify-between gap-4 mt-auto"
    >
      <span class="text-xs text-zinc-500 font-bold uppercase tracking-widest">
        {{ filteredEmployees.length }} Registros
      </span>
      
      <div class="flex items-center gap-2">
        <button class="h-9 px-4 rounded-lg text-xs font-bold text-zinc-400 bg-zinc-50 cursor-not-allowed transition-colors" disabled>
          Anterior
        </button>
        <button class="h-9 w-9 rounded-lg bg-brand-primary text-white text-xs font-bold shadow-sm shadow-brand-primary/20 hover:bg-brand-primary/90 transition-all cursor-pointer">1</button>
        <button class="h-9 px-4 rounded-lg text-xs font-bold text-zinc-700 bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 transition-all shadow-sm cursor-pointer">
          Próximo
        </button>
      </div>
    </div>
  </div>
</template>