<script setup lang="ts">
import { ref, computed, watch, type Component } from 'vue';
import { Smartphone, ClipboardList, Package } from 'lucide-vue-next';

import OSEquipmentTab from './OSEquipmentTab.vue';
import OSDiagnosticoTab from './OSDiagnosticoTab.vue';
import OSServicesTab from './OSServicesTab.vue';
import type { EquipamentoFormData } from '../../composables/modal/useOSFormAdapter';
import { useOSFormView } from '../../context/useOSFormView.context';

type TabType = 'equipamento' | 'diagnostico' | 'servicos';

const view = useOSFormView();

const activeTab = ref<TabType>('equipamento');

watch(() => view.isOpen.value, (open) => {
  if (open) {
    activeTab.value = 'equipamento';
  }
});

const allTabs: { id: TabType; label: string; icon: Component }[] = [
  { id: 'equipamento', label: 'Equipamento', icon: Smartphone },
  { id: 'diagnostico', label: 'Diagnóstico', icon: ClipboardList },
  { id: 'servicos', label: 'Serviços e Peças', icon: Package },
];

const visibleTabs = computed(() =>
  view.isCreateMode.value ? allTabs.filter((tab) => tab.id !== 'diagnostico') : allTabs,
);

const equipamentoModel = computed<EquipamentoFormData>({
  get: () => view.equipamentoFormData.value,
  set: (value) => view.setEquipamentoFormData(value),
});
</script>

<template>
  <div>
    <div class="flex p-1 mb-4 bg-slate-100 rounded-xl gap-1">
      <button
        v-for="tab in visibleTabs"
        :key="tab.id"
        type="button"
        :class="[
          'flex-1 flex items-center justify-center gap-2 py-2 px-3 text-sm font-bold rounded-lg transition-all',
          activeTab === tab.id
            ? 'bg-white text-brand-primary shadow-sm'
            : 'text-slate-500 hover:text-slate-700',
        ]"
        @click="activeTab = tab.id"
      >
        <component :is="tab.icon" :size="14" />
        {{ tab.label }}
      </button>
    </div>

    <fieldset :disabled="view.isStructureLocked.value" class="contents">
      <div class="min-h-125">
        <OSEquipmentTab
          v-if="activeTab === 'equipamento'"
          v-model="equipamentoModel"
          :equipamentos-historico="view.equipamentosHistorico.value"
          :selected-historico="view.selectedHistorico.value"
          :is-locked="view.isStructureLocked.value"
          :is-create-mode="view.isCreateMode.value"
          @update:selected-historico="view.setSelectedHistorico"
          @apply-historico="view.applyEquipamentoHistorico"
        />

        <OSDiagnosticoTab
          v-if="activeTab === 'diagnostico'"
          :diagnostico="view.currentDiagnostico.value"
          :os-numero="view.currentOSData.value?.numero_os"
          :fotos="view.currentOSData.value?.fotos ?? []"
          :pending-photos="view.pendingPhotos.value"
          :is-locked="view.isStructureLocked.value"
          @update:diagnostico="view.handleDiagnosticoUpdate"
          @add-photo="view.handleAddPhoto"
          @remove-pending="view.handleRemovePending"
          @photo-change="view.handlePhotoChange"
        />

        <OSServicesTab
          v-if="activeTab === 'servicos'"
          :itens="view.displayItems.value"
          :is-locked="view.isItemsLocked.value"
          @add-item="view.openAddItemModal"
          @edit-item="view.openEditItemModal"
          @remove-item="view.handleRemoveItem"
        />
      </div>
    </fieldset>
  </div>
</template>
