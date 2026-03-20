<!--
===========================================================================
ARQUIVO: OrdemServicoView.vue
MODULO: Ordem de Servico
DESCRICAO: View principal do modulo de OS. Contem navegacao por tabs entre
           Ordens de Servico, Orcamentos e Cadastro de Servicos.
===========================================================================

TABS:
1. Ordens de Servico (ordens) - Listagem e gerenciamento de OS
2. Orcamentos (orcamentos) - Listagem e criacao de orcamentos
3. Cadastro de Servicos (servicos) - Catalogo de servicos disponiveis

LAYOUT:
- Header: Titulo dinamico + Tabs de navegacao + Botao de acao
- Content: Componente da tab ativa

BOTOES DE ACAO (variam por tab):
- Tab Ordens: "Nova OS" -> abre fluxo de criacao
- Tab Orcamentos: "Novo Orcamento" -> abre modal de orcamento
- Tab Servicos: "Novo Servico" -> abre modal de servico

COMUNICACAO COM TABS:
- Refs para acessar metodos expostos pelos componentes filhos
- Evento os-created no OrcamentosTab para navegar para tab de OS
===========================================================================
-->
<script setup lang="ts">
import { ref, computed, type Component } from 'vue';
import { ClipboardList, Wrench, Plus, FileText } from 'lucide-vue-next';
import OrdensServicoTab from './tabs/OrdensServicoTab.vue';
import ServicosTab from './tabs/ServicosTab.vue';
import OrcamentosTab from '@/modules/orcamento/components/OrcamentosTab.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';

type TabType = 'ordens' | 'servicos' | 'orcamentos';

const activeTab = ref<TabType>('ordens');
const tabComponentRef = ref();
const servicosTabRef = ref();
const orcamentosTabRef = ref();

const tabs: { id: TabType; label: string; icon: Component }[] = [
  { id: 'ordens', label: 'Ordens de Serviço', icon: ClipboardList },
  { id: 'orcamentos', label: 'Orçamentos', icon: FileText },
  { id: 'servicos', label: 'Cadastro de Serviços', icon: Wrench },
];

const pageTitle = computed(() => {
  const currentTab = tabs.find(t => t.id === activeTab.value);
  return currentTab?.label || 'Ordem de Serviço';
});

function setTab(tab: TabType) {
  activeTab.value = tab;
}

function handleNewOS() {
  if (tabComponentRef.value?.handleOpenNovaOS) {
    tabComponentRef.value.handleOpenNovaOS();
  }
}

function handleNewServico() {
  if (servicosTabRef.value?.handleOpenModal) {
    servicosTabRef.value.handleOpenModal();
  }
}

function handleNewOrcamento() {
  if (orcamentosTabRef.value?.handleNewOrcamento) {
    orcamentosTabRef.value.handleNewOrcamento();
  }
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <!-- Header: Title (Left) + Tabs & Actions (Right) -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <!-- Title -->
      <h2 class="text-xl font-bold text-zinc-800">{{ pageTitle }}</h2>

      <!-- Right Side: Tabs + Action Button -->
      <div class="flex items-center gap-4 self-end md:self-auto">
        <!-- Tabs -->
        <div
          class="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm text-xs font-semibold"
        >
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="[
              'flex items-center gap-2 px-3 md:px-4 py-1.5 md:py-2 rounded-lg transition-all duration-200',
              activeTab === tab.id
                ? 'bg-zinc-900 text-white shadow-sm'
                : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50',
            ]"
            @click="setTab(tab.id)"
          >
            <component :is="tab.icon" :size="14" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Action Button (Nova OS) -->
        <BaseButton 
          v-if="activeTab === 'ordens'" 
          @click="handleNewOS"
        >
          <Plus :size="18" />
          Nova OS
        </BaseButton>

        <!-- Action Button (Novo Orcamento) -->
        <BaseButton 
          v-if="activeTab === 'orcamentos'" 
          @click="handleNewOrcamento"
        >
          <Plus :size="18" />
          Novo Orçamento
        </BaseButton>

        <!-- Action Button (Novo Servico) -->
        <BaseButton 
          v-if="activeTab === 'servicos'" 
          @click="handleNewServico"
        >
          <Plus :size="18" />
          Novo Serviço
        </BaseButton>
      </div>
    </div>

    <!-- Tab Content -->
    <OrdensServicoTab v-if="activeTab === 'ordens'" ref="tabComponentRef" />
    <OrcamentosTab 
      v-else-if="activeTab === 'orcamentos'" 
      ref="orcamentosTabRef" 
      @os-created="() => setTab('ordens')"
    />
    <ServicosTab v-else-if="activeTab === 'servicos'" ref="servicosTabRef" />
  </div>
</template>
