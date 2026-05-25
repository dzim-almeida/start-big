<script setup lang="ts">
/**
 * ===========================================================================
 * ARQUIVO: OrdensServicoTab.vue
 * MODULO: Ordem de Servico
 * DESCRICAO: Tab principal de listagem e gerenciamento de Ordens de Servico.
 * ===========================================================================
 *
 * FLUXO DE NOVA OS:
 * 1. Usuario clica em "Nova OS"
 * 2. Abre modal de busca de cliente (OSClienteSearchModal)
 * 3. Usuario seleciona cliente ou cadastra novo
 * 4. Abre formulario de OS (OSFormModal) com cliente pre-selecionado
 * ===========================================================================
 */

import { ref } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';
import OSTable from '../../components/listagem/OSTable.vue';
import OSFormModal from '../../components/cadastro/OSFormModal.vue';
import OSFinalizarModal from '../../components/cadastro/OSFinalizarModal.vue';
import OSClienteSearchModal from '../../components/cadastro/OSClienteSearchModal.vue';
import OSCancelModal from '../../components/cadastro/OSCancelModal.vue';
import OSStats from '../../components/listagem/OSStats.vue';
import OSPrintTemplate from '../../components/print/OSPrintTemplate.vue';
import { useOrdensServico, useOSActions } from '../../composables';
import { ordemServicoService } from '../../services/ordemServico.service';
import type {
  OrdemServicoRead,
  OrdemServicoListRead,
  OrdemServicoStatus,
} from '../../types/ordemServico.types';
import type { Cliente } from '@/modules/clientes/types/clientes.types';
import { useToast } from '@/shared/composables/useToast';

// ===========================================================================
// COMPOSABLES
// ===========================================================================

const toast = useToast();
const queryClient = useQueryClient();

const {
  ordensServico,
  stats,
  activeFilterStatus,
  searchQuery,
  isLoading,
  error,
  setFilterStatus,
  setSearch,
  // Paginação
  currentPage,
  totalPages,
  totalItems,
  setPage,
} = useOrdensServico();

const { 
    cancelarMutation, 
    toggleAtivoMutation,
    isPending: isActionsPending 
} = useOSActions();

// ===========================================================================
// ESTADOS DOS MODAIS
// ===========================================================================

// Modal de busca de cliente (primeiro passo para criar OS)
const isClienteSearchModalOpen = ref(false);

// Modal de formulario da OS (segundo passo)
const isFormModalOpen = ref(false);

// Modal de finalizacao da OS
const isFinalizarModalOpen = ref(false);

// Modal de cancelamento
const isCancelModalOpen = ref(false);

// OS selecionada para edicao/visualizacao
const selectedOS = ref<OrdemServicoRead | null>(null);

// Cliente selecionado para nova OS
const selectedCliente = ref<Cliente | null>(null);

// OS para impressao
const osToPrint = ref<OrdemServicoRead | null>(null);
const printType = ref<'ENTRADA' | 'SAIDA' | 'CANCELAMENTO' | null>(null);

const osToCancel = ref<OrdemServicoListRead | null>(null);
const autoShowReopen = ref(false);

// ===========================================================================
// OPTIONS
// ===========================================================================



// ===========================================================================
// MUTATIONS
// ===========================================================================



// ===========================================================================
// HANDLERS - FILTROS
// ===========================================================================

function handleSearch(value: string) {
  setSearch(value);
}

function handleStatusChange(value: string | undefined | null) {
  // O componente pode emitir string vazia ou valor direto
  setFilterStatus((value || 'todos') as OrdemServicoStatus | 'todos');
}

// ===========================================================================
// HANDLERS - FLUXO DE NOVA OS
// ===========================================================================

/**
 * Abre modal de busca de cliente (primeiro passo)
 */
function handleOpenNovaOS() {
  selectedOS.value = null;
  selectedCliente.value = null;
  isClienteSearchModalOpen.value = true;
}

/**
 * Fecha modal de busca de cliente
 */
function handleCloseClienteSearch() {
  isClienteSearchModalOpen.value = false;
}

/**
 * Callback quando cliente e selecionado no modal de busca
 * Fecha busca e abre formulario com cliente pre-selecionado
 */
function handleClienteSelected(cliente: Cliente) {
  selectedCliente.value = cliente;
  isClienteSearchModalOpen.value = false;
  isFormModalOpen.value = true;
}

/**
 * Callback quando usuario quer cadastrar novo cliente
 * Por enquanto apenas fecha o modal - futuramente abrir modal de cliente
 */
function handleNewCliente() {
  toast.info('Funcionalidade de cadastro rapido em desenvolvimento');
  // TODO: Abrir modal de cadastro de cliente
  // Apos cadastro, chamar handleClienteSelected com o novo cliente
}

/**
 * Callback quando usuario quer trocar cliente no formulario
 * Fecha formulario e reabre busca
 */
function handleChangeCliente() {
  isFormModalOpen.value = false;
  isClienteSearchModalOpen.value = true;
}

// ===========================================================================
// HANDLERS - FORM MODAL
// ===========================================================================

function handleCloseFormModal() {
  isFormModalOpen.value = false;
  selectedOS.value = null;
  selectedCliente.value = null;
  autoShowReopen.value = false;
}

function handleCloseFinalizarModal() {
  isFinalizarModalOpen.value = false;
  selectedOS.value = null;
}

// ===========================================================================
// HANDLERS - ACOES DA TABELA
// ===========================================================================

async function handleView(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.id);
    selectedOS.value = osCompleta;
    selectedCliente.value = null; // Em modo edicao, cliente vem da OS
    isFormModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar detalhes da OS');
  }
}

async function handleEdit(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.id);
    selectedOS.value = osCompleta;
    selectedCliente.value = null; // Em modo edicao, cliente vem da OS
    isFormModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar OS para edicao');
  }
}

async function handleFinalizar(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.id);
    selectedOS.value = osCompleta;
    isFinalizarModalOpen.value = true;
  } catch {
    toast.error('Erro ao carregar OS');
  }
}

// ===========================================================================
// HANDLERS - CANCELAMENTO
// ===========================================================================

function handleCancelar(os: OrdemServicoListRead) {
  osToCancel.value = os;
  isCancelModalOpen.value = true;
}

function handleCloseCancelModal() {
  isCancelModalOpen.value = false;
  osToCancel.value = null;
}

function handleConfirmCancel(payload: { motivo: string; print: boolean }) {
  if (osToCancel.value) {
    const osRef = osToCancel.value; // Store ref
    cancelarMutation.mutate(
        { id: osRef.id, motivo: payload.motivo },
        { 
            onSuccess: () => {
                if (payload.print) {
                     printCancelamento(osRef, payload.motivo);
                }
                handleCloseCancelModal();
            }
        }
    );
  }
}

async function printCancelamento(os: OrdemServicoListRead, motivo: string) {
   try {
    const osCompleta = await ordemServicoService.getById(os.id);
    // Adaptação para passar motivo caso o template suporte ou via propriedade extra
    const osComMotivo = { ...osCompleta, motivo_cancelamento: motivo }; 
    
    osToPrint.value = osComMotivo as any; 
    printType.value = 'CANCELAMENTO';
    
    setTimeout(() => {
      window.print();
      setTimeout(() => {
        osToPrint.value = null;
        printType.value = null; 
        queryClient.invalidateQueries({ queryKey: ['ordens-servico'] }); // Ensure list updates status
      }, 500);
    }, 100);
  } catch {
    toast.error('Erro ao preparar impressão do cancelamento');
  }
}

// ===========================================================================
// HANDLERS - OUTROS
// ===========================================================================

function handleReabrir(os: OrdemServicoListRead) {
  // Ao clicar em reabrir na tabela, abrimos o formulario.
  // Como a OS esta finalizada, setamos para abrir diretas as opcoes
  autoShowReopen.value = true;
  handleEdit(os);
}

function handleToggleStatus(os: OrdemServicoListRead) {
  toggleAtivoMutation.mutate(os.id);
}

async function handlePrintOS(os: OrdemServicoListRead) {
  try {
    const osCompleta = await ordemServicoService.getById(os.id);
    osToPrint.value = osCompleta;
    
    // Define o tipo de impressao baseado no status
    if (osCompleta.status === 'CANCELADA') {
        printType.value = 'CANCELAMENTO';
    } else {
        printType.value = 'SAIDA';
    }
    
    // Aguarda renderizacao do template e imprime
    setTimeout(() => {
      window.print();
      // Limpa apos impressao (opcional, mas bom para evitar flicker)
      setTimeout(() => {
        osToPrint.value = null;
        printType.value = null;
      }, 500);
    }, 100);
  } catch {
    toast.error('Erro ao preparar impressão');
  }
}

defineExpose({
  handleOpenNovaOS,
});
</script>

<template>
  <div class="space-y-6">
    <!-- Stats -->
    <OSStats :stats="stats" :loading="isLoading" />

    <!-- Error State -->
    <div
      v-if="error"
      class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700"
    >
      Erro ao carregar ordens de servico. Verifique sua conexao e tente novamente.
    </div>

    <!-- Table -->
    <OSTable
      :ordens-servico="ordensServico"
      :is-loading="isLoading"
      :search-query="searchQuery"
      :active-filter="activeFilterStatus"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      @view="handleView"
      @edit="handleEdit"
      @finalizar="handleFinalizar"
      @cancelar="handleCancelar"
      @reabrir="handleReabrir"
      @print="handlePrintOS"
      @toggle-status="handleToggleStatus"
      @search="handleSearch"
      @filter-change="handleStatusChange"
      @update:current-page="setPage"
    />

    <!-- Modal: Busca de Cliente -->
    <OSClienteSearchModal
      :is-open="isClienteSearchModalOpen"
      @close="handleCloseClienteSearch"
      @select-cliente="handleClienteSelected"
      @new-cliente="handleNewCliente"
    />

    <!-- Modal: Formulario -->
    <OSFormModal
      :is-open="isFormModalOpen"
      :ordem-servico="selectedOS"
      :selected-cliente="selectedCliente"
      :auto-show-reopen="autoShowReopen"
      @close="handleCloseFormModal"
      @change-cliente="handleChangeCliente"
      @saved="(os) => selectedOS = os"
    />

    <!-- Modal: Finalizar -->
    <OSFinalizarModal
      :is-open="isFinalizarModalOpen"
      :ordem-servico="selectedOS"
      @close="handleCloseFinalizarModal"
    />

    <!-- Modal: Cancelar -->
    <OSCancelModal 
      :is-open="isCancelModalOpen"
      :os="osToCancel"
      :is-loading="isActionsPending"
      @close="handleCloseCancelModal"
      @confirm="handleConfirmCancel"
    />

    <!-- Template Invisivel para Impressao -->
    <OSPrintTemplate
      v-if="osToPrint"
      :ordem-servico="osToPrint"
      :type="printType || 'SAIDA'"
    />
  </div>
</template>

<style scoped>
.animate-fadeInScale {
  animation: fadeInScale 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
