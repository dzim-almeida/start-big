<!--
===========================================================================
ARQUIVO: OSTable.vue
MODULO: Ordem de Servico
DESCRICAO: Componente de listagem de OS em formato de cards. Inclui busca,
           filtro por status e acoes contextuais por item.
===========================================================================

PROPS:
- ordensServico: Lista de OS para exibicao
- isLoading: Estado de carregamento
- searchQuery: Texto atual de busca
- activeFilter: Filtro de status ativo
- currentPage, totalPages, totalItems: Controle de paginacao

EMITS:
- view: Visualizar detalhes da OS
- edit: Editar OS (somente se nao finalizada/cancelada)
- finalizar: Abrir modal de finalizacao
- cancelar: Abrir modal de cancelamento
- reabrir: Reabrir OS finalizada/cancelada
- print: Imprimir OS
- search: Texto de busca alterado
- filterChange: Filtro de status alterado
- update:currentPage: Pagina alterada

ACOES POR STATUS:
- ABERTA/EM_ANDAMENTO: Ver, Editar, Finalizar, Cancelar
- FINALIZADA/CANCELADA: Ver, Reabrir, Imprimir

LAYOUT:
- Toolbar: Campo de busca + Dropdown de filtro
- Cards: Badge OS | Cliente + Equipamento + Status | Acoes
- Paginacao via BaseTableContainer
===========================================================================
-->
<script setup lang="ts">
import { Eye, Pencil, CheckCircle, XCircle, RotateCcw, Printer, Search, Filter } from 'lucide-vue-next';
import type { OrdemServicoListRead } from '../../types/ordemServico.types';
import { OS_STATUS_OPTIONS } from '../../constants';
import { getStatusLabel, getClienteNome } from '../../utils';
import { formatCurrency } from '@/shared/utils/finance';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import { ref, onMounted, onUnmounted, computed } from 'vue';

interface Props {
  ordensServico: OrdemServicoListRead[];
  isLoading?: boolean;
  searchQuery?: string;
  activeFilter?: string;
  totalPages?: number;
  currentPage?: number;
  totalItems?: number;
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  searchQuery: '',
  activeFilter: 'todos',
  totalPages: 1,
  currentPage: 1,
  totalItems: 0,
});

const emit = defineEmits<{
  view: [os: OrdemServicoListRead];
  edit: [os: OrdemServicoListRead];
  finalizar: [os: OrdemServicoListRead];
  cancelar: [os: OrdemServicoListRead];
  reabrir: [os: OrdemServicoListRead];
  print: [os: OrdemServicoListRead];
  toggleStatus: [os: OrdemServicoListRead];
  search: [value: string];
  filterChange: [value: string];
  'update:currentPage': [page: number];
}>();

const isFilterOpen = ref(false);
const filterContainerRef = ref<HTMLDivElement | null>(null);

function toggleFilter() {
    isFilterOpen.value = !isFilterOpen.value;
}

function handleClickOutside(event: MouseEvent) {
    if (filterContainerRef.value && !filterContainerRef.value.contains(event.target as Node)) {
        isFilterOpen.value = false;
    }
}

// Compute active label
const activeFilterLabel = computed(() => {
    if (props.activeFilter === 'todos') return 'Todos os status';
    const option = statusOptions.find(o => o.value === props.activeFilter);
    return option ? option.label : props.activeFilter;
});

onMounted(() => {
    document.addEventListener('mousedown', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('mousedown', handleClickOutside);
});

function formatDate(dateValue: string | Date): string {
  return new Date(dateValue).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  });
}

function getStatusConfig(status: string) {
  const configs: Record<string, { bg: string; text: string; dot: string }> = {
    ABERTA: { bg: 'bg-brand-primary-light', text: 'text-brand-primary', dot: 'bg-brand-primary' },
    EM_ANDAMENTO: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
    AGUARDANDO_PECAS: { bg: 'bg-orange-50', text: 'text-orange-700', dot: 'bg-orange-500' },
    AGUARDANDO_APROVACAO: { bg: 'bg-purple-50', text: 'text-purple-700', dot: 'bg-purple-500' },
    AGUARDANDO_RETIRADA: { bg: 'bg-indigo-50', text: 'text-indigo-700', dot: 'bg-indigo-500' },
    FINALIZADA: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
    CANCELADA: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
  };
  return configs[status] || { bg: 'bg-zinc-50', text: 'text-zinc-700', dot: 'bg-zinc-500' };
}

// Extrai o numero sequencial da OS (ex: "OS-2026-000001" -> "01")
function getOSSequence(numero: string): string {
  if (!numero) return '00';
  // Formato: OS-AAAA-NNNNNN -> pega os ultimos 6 digitos e remove zeros a esquerda
  const parts = numero.split('-');
  if (parts.length === 3) {
    const seq = parseInt(parts[2], 10);
    return String(seq).padStart(2, '0');
  }
  return '00';
}

const statusOptions = [
  { value: 'todos', label: 'Todos os status' },
  ...OS_STATUS_OPTIONS,
];

function handleView(os: OrdemServicoListRead) {
  emit('view', os);
}

function handleEdit(os: OrdemServicoListRead) {
  emit('edit', os);
}

function handleFinalizar(os: OrdemServicoListRead) {
  emit('finalizar', os);
}

function handleCancelar(os: OrdemServicoListRead) {
  emit('cancelar', os);
}

function handleReabrir(os: OrdemServicoListRead) {
  emit('reabrir', os);
}

function handlePrint(os: OrdemServicoListRead) {
  emit('print', os);
}

function handleSearch(event: Event) {
  const target = event.target as HTMLInputElement;
  emit('search', target.value);
}

function handleFilterChange(value: string) {
  emit('filterChange', value);
  isFilterOpen.value = false;
}
</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-empty="ordensServico.length === 0"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    item-label="OS"
    item-label-plural="OS"
    empty-title="Nenhuma OS encontrada"
    empty-description='Clique em "Nova OS" para criar uma ordem de servico'
    @update:current-page="emit('update:currentPage', $event)"
  >
    <!-- Toolbar -->
    <template #toolbar>
        <div class="flex flex-1 w-full gap-4">
            <!-- Busca -->
            <div class="relative flex-1 max-w-md">
               <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                 <Search :size="18" class="text-zinc-400" />
               </div>
               <input
                 type="text"
                 :value="searchQuery"
                 placeholder="Buscar por número, cliente..."
                 class="w-full pl-11 pr-4 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary transition-all placeholder:text-zinc-400"
                 @input="handleSearch"
               />
            </div>

            <!-- Filtro -->
            <div class="w-auto">
               <div class="relative" ref="filterContainerRef">
                 <BaseButton 
                    variant="secondary"
                    @click="toggleFilter"
                    class="flex items-center justify-between gap-2 relative min-w-36"
                    title="Filtrar por status"
                 >
                    <div class="flex items-center gap-2 w-full justify-between">
                        <span class="text-sm font-medium">{{ activeFilterLabel }}</span>
                        <Filter :size="16" class="text-zinc-400" />
                    </div>
                 </BaseButton>

                 <!-- Dropdown -->
                 <div 
                    v-if="isFilterOpen"
                    class="absolute right-0 top-full mt-2 w-56 bg-white border border-zinc-100 rounded-xl shadow-xl z-50 py-2 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 origin-top-right ring-1 ring-zinc-200"
                 >
                    <div class="px-4 py-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">
                        Filtrar Status
                    </div>
                    
                    <div class="h-px bg-zinc-100 mx-0 mb-1"></div>

                    <button
                        v-for="opt in statusOptions"
                        :key="opt.value"
                        @click="handleFilterChange(opt.value)"
                        class="w-full px-4 py-2.5 text-sm text-left flex items-center justify-between hover:bg-zinc-50 transition-colors group"
                        :class="activeFilter === opt.value ? 'text-brand-primary font-medium' : 'text-zinc-600 font-medium'"
                    >
                        <span>{{ opt.label }}</span>
                        <!-- Dot indicator for active -->
                        <div 
                            v-if="activeFilter === opt.value" 
                            class="w-2 h-2 rounded-full bg-brand-primary"
                        ></div>
                    </button>
                 </div>
               </div>
            </div>
        </div>
    </template>

    <!-- Cards List (Default Slot) -->
    <div class="divide-y divide-zinc-100">
      <div
        v-for="os in ordensServico"
        :key="os.id"
        class="p-4 hover:bg-zinc-50/50 transition-colors"
      >
        <div class="flex items-start gap-4">
          <!-- OS Number Badge -->
          <div class="shrink-0">
            <div class="w-14 h-14 bg-brand-primary rounded-xl flex flex-col items-center justify-center text-white shadow-sm">
              <span class="text-[10px] font-medium opacity-80">OS</span>
              <span class="text-lg font-bold -mt-1">{{ getOSSequence(os.numero) }}</span>
            </div>
          </div>

          <!-- Main Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <!-- Cliente e Equipamento -->
                <h4 class="font-semibold text-zinc-900 truncate">
                  {{ getClienteNome(os.cliente) }}
                </h4>
                <p class="text-sm text-zinc-500 truncate mt-0.5">
                  {{ os.equipamento }}
                </p>
              </div>

              <!-- Status Badge -->
              <div
                :class="[
                  'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold shrink-0',
                  getStatusConfig(os.status).bg,
                  getStatusConfig(os.status).text,
                ]"
              >
                <span
                  :class="['w-1.5 h-1.5 rounded-full', getStatusConfig(os.status).dot]"
                ></span>
                {{ getStatusLabel(os.status) }}
              </div>
            </div>

            <!-- Info Row -->
            <div class="flex items-center gap-4 mt-3 text-xs">
              <span class="text-zinc-400">
                {{ formatDate(os.data_criacao) }}
              </span>
              <span v-if="os.valor_total > 0" class="font-semibold text-brand-primary">
                {{ formatCurrency(os.valor_total) }}
              </span>
              <span v-if="os.numero" class="text-zinc-400 font-mono">
                {{ os.numero }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 shrink-0">
            <BaseButton
              variant="ghost"
              size="sm"
              class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary-light"
              title="Ver detalhes"
              @click="handleView(os)"
            >
              <Eye :size="18" />
            </BaseButton>

            <BaseButton
              v-if="os.status !== 'FINALIZADA' && os.status !== 'CANCELADA'"
              variant="ghost"
              size="sm"
              class="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100"
              title="Editar"
              @click="handleEdit(os)"
            >
              <Pencil :size="18" />
            </BaseButton>

            <BaseButton
              v-if="os.status !== 'FINALIZADA' && os.status !== 'CANCELADA'"
              variant="ghost"
              size="sm"
              class="p-2 text-zinc-400 hover:text-emerald-600 hover:bg-emerald-50"
              title="Finalizar OS"
              @click="handleFinalizar(os)"
            >
              <CheckCircle :size="18" />
            </BaseButton>

            <BaseButton
              v-if="os.status !== 'FINALIZADA' && os.status !== 'CANCELADA'"
              variant="ghost"
              size="sm"
              class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50"
              title="Cancelar OS"
              @click="handleCancelar(os)"
            >
              <XCircle :size="18" />
            </BaseButton>

            <!-- Botao Reabrir - apenas para OS finalizadas ou canceladas -->
            <BaseButton
              v-if="os.status === 'FINALIZADA' || os.status === 'CANCELADA'"
              variant="ghost"
              size="sm"
              class="p-2 text-zinc-400 hover:text-amber-600 hover:bg-amber-50"
              title="Reabrir OS"
              @click="handleReabrir(os)"
            >
              <RotateCcw :size="18" />
            </BaseButton>

            <!-- Botao Imprimir - apenas para OS finalizadas -->
            <BaseButton
              v-if="os.status === 'FINALIZADA' || os.status === 'CANCELADA'"
              variant="ghost"
              size="sm"
              class="p-2 text-zinc-400 hover:text-brand-primary hover:bg-brand-primary-light"
              title="Imprimir OS"
              @click="handlePrint(os)"
            >
              <Printer :size="18" />
            </BaseButton>
          </div>
        </div>
      </div>
    </div>
  </BaseTableContainer>
</template>


