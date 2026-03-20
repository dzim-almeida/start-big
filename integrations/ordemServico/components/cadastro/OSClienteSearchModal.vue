<script setup lang="ts">
/**
 * ===========================================================================
 * MODULO: Ordem de Servico
 * COMPONENT: OSClienteSearchModal.vue
 * DESCRICAO: Modal de busca de cliente.
 * ===========================================================================
 */

import { toRef, ref } from 'vue';
import { Search, User, Plus } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/commons/BaseInput/BaseInput.vue';
import ClientListItem from '@/modules/clientes/components/ClientListItem.vue';
import QuickClientForm from '@/modules/clientes/components/QuickClientForm.vue';
import type { Cliente } from '@/modules/clientes/types/clientes.types';

// Composables
import { useOSClientSearch } from '../../composables/useOSClientSearch';

interface Props {
  isOpen: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  selectCliente: [cliente: Cliente];
  newCliente: [];
}>();

// ===================================
// LOGICA DE BUSCA
// ===================================
const { 
  searchQuery, 
  selectedClienteId, 
  filteredClientes, 
  isLoading, 
  reset: resetSearch 
} = useOSClientSearch(toRef(props, 'isOpen'));

// ===================================
// ESTADO DE CRIACAO
// ===================================
const isCreating = ref(false);
const quickFormRef = ref<InstanceType<typeof QuickClientForm> | null>(null);

function toggleCreateMode() {
  isCreating.value = !isCreating.value;
  if (!isCreating.value) {
    quickFormRef.value?.reset();
  }
}

// ===================================
// HANDLERS
// ===================================

function handleClose() {
  resetSearch();
  isCreating.value = false;
  quickFormRef.value?.reset();
  emit('close');
}

function handleSelectCliente(cliente: Cliente) {
  emit('selectCliente', cliente);
}

async function handleSubmitCreate() {
  if (!quickFormRef.value) return;
  
  const novoCliente = await quickFormRef.value.submit();
  
  if (novoCliente) {
    handleSelectCliente(novoCliente);
    // Modal fecha automaticamente pelo selectCliente no pai, ou podemos fechar aqui?
    // O pai (OrdensServicoTab) fecha o modal ao receber selectCliente.
    isCreating.value = false;
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="isCreating ? 'Novo Cadastro' : 'Selecionar Cliente'"
    :subtitle="isCreating ? 'Preencha os dados básicos para continuar' : 'Busque o cliente para iniciar a Ordem de Serviço'"
    size="lg"
    @close="handleClose"
  >
    <!-- MODO BUSCA -->
    <div v-if="!isCreating">
      
      <!-- Campo de Busca -->
      <div class="mb-6">
        <BaseInput
           v-model="searchQuery"
           placeholder="Buscar por nome, CPF/CNPJ ou Nº Série..."
           :left-icon="Search"
           autofocus
        />
      </div>

      <!-- Lista de Clientes -->
      <div class="space-y-3 max-h-100 overflow-y-auto px-1 custom-scrollbar">
        <!-- Loading -->
        <div v-if="isLoading" class="flex flex-col items-center justify-center py-12 space-y-3">
          <div class="animate-spin rounded-full h-8 w-8 border-2 border-brand-primary border-t-transparent"></div>
          <span class="text-sm text-zinc-400 font-medium">Buscando clientes...</span>
        </div>

        <!-- Lista vazia -->
        <div
          v-else-if="filteredClientes.length === 0"
          class="text-center py-16 px-6 bg-zinc-50 border border-dashed border-zinc-200 rounded-2xl"
        >
          <div class="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm ring-1 ring-zinc-100">
            <User :size="32" class="text-zinc-300" />
          </div>
          <h3 class="text-zinc-900 font-semibold mb-1">Nenhum cliente encontrado</h3>
          <p class="text-zinc-500 text-sm mb-6 max-w-xs mx-auto">
            {{ searchQuery ? `Não encontramos clientes com "${searchQuery}"` : 'Comece digitando para buscar um cliente' }}
          </p>
          <BaseButton
            variant="dashed"
            @click="toggleCreateMode()"
          >
            <Plus :size="16" class="mr-2" />
            Cadastrar Novo Cliente
          </BaseButton>
        </div>

        <!-- Cards de Clientes (Usando Componente Extraido) -->
        <ClientListItem
          v-else
          v-for="cliente in filteredClientes"
          :key="cliente.id"
          :cliente="cliente"
          :is-selected="selectedClienteId === cliente.id"
          @select="handleSelectCliente(cliente)"
        />
        
      </div> <!-- Fim Lista Clientes -->
    </div>

    <!-- MODO CRIACAO (Usando Componente Extraido) -->
    <QuickClientForm
      v-else
      ref="quickFormRef"
    />

    <!-- Footer Dinamico -->
    <template #footer>
      <div v-if="!isCreating" class="flex items-center justify-between w-full">
        <BaseButton 
          variant="dashed"
          @click="toggleCreateMode()"
        >
          <Plus :size="16" class="mr-2" />
          Novo Cliente
        </BaseButton>

        <div class="flex items-center gap-3">
          <p class="text-xs text-zinc-400 mr-2 hidden sm:block">
            {{ filteredClientes.length }} clientes
          </p>
          <BaseButton variant="secondary" @click="handleClose">
            Cancelar
          </BaseButton>
        </div>
      </div>

      <div v-else class="flex items-center justify-between w-full">
        <BaseButton
          variant="ghost"
           class="text-sm font-medium text-zinc-500 hover:text-zinc-800 transition-colors"
          @click="toggleCreateMode()"
        >
          Voltar para busca
        </BaseButton>
        <!-- isSubmitting eh acessado reativamente via ref do form, ou precisamos expor? 
             O ref nao eh reativo profundo para propriedades internas dessa forma no template as vezes.
             Para garantir, o quickFormRef pode expor isSubmitting. Mas para usar no template: quickFormRef?.isSubmitting
        -->
        <BaseButton 
           variant="primary" 
           :is-loading="quickFormRef?.isSubmitting" 
           @click="handleSubmitCreate"
        >
          <Plus :size="18" class="mr-2" />
          Salvar e Selecionar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

<style scoped>
/* Scrollbar removida daqui, agora global */
</style>
