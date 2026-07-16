<script setup lang="ts">
import { ref, computed, watch, type Component } from 'vue';
import { Smartphone, Car, ClipboardCheck, ClipboardList, Package } from 'lucide-vue-next';

import OSObjetoTab from './OSObjetoTab.vue';
import OSVistoriaTab from '@/modules/order-service/segmentos/oficina/components/OSVistoriaTab.vue';
import OSDiagnosticoTab from './OSDiagnosticoTab.vue';
import OSServicesTab from './OSServicesTab.vue';
import type { ObjetoFormData } from '../../composables/modal/useOSFormAdapter';
import { useOSFormView } from '../../context/useOSFormView.context';
import { useSegmento } from '@/shared/composables/useSegmento';
import { useObjetoLabels } from '@/modules/order-service/shared/segmento/useObjetoLabels';

type TabType = 'objeto' | 'vistoria' | 'diagnostico' | 'servicos';

const view = useOSFormView();

// Rótulo/ícone da aba do objeto seguem o segmento (Veículo/Equipamento).
const { isOficinaMecanica } = useSegmento();
const { labelSingular } = useObjetoLabels();

const activeTab = ref<TabType>('objeto');

watch(() => view.isOpen.value, (open) => {
  if (open) {
    activeTab.value = 'objeto';
  }
});

const allTabs = computed<{ id: TabType; label: string; icon: Component }[]>(() => {
  const tabs: { id: TabType; label: string; icon: Component }[] = [
    { id: 'objeto', label: labelSingular.value, icon: isOficinaMecanica.value ? Car : Smartphone },
  ];
  // Vistoria: exclusiva de oficina (checklist da ficha de entrada).
  if (isOficinaMecanica.value) {
    tabs.push({ id: 'vistoria', label: 'Vistoria', icon: ClipboardCheck });
  }
  tabs.push(
    { id: 'diagnostico', label: 'Diagnóstico', icon: ClipboardList },
    { id: 'servicos', label: 'Serviços e Peças', icon: Package },
  );
  return tabs;
});

const visibleTabs = computed(() =>
  view.isCreateMode.value ? allTabs.value.filter((tab) => tab.id !== 'diagnostico') : allTabs.value,
);

const objetoModel = computed<ObjetoFormData>({
  get: () => view.objetoFormData.value,
  set: (value) => view.setObjetoFormData(value),
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

    <div class="min-h-125">
      <fieldset v-if="activeTab !== 'diagnostico'" :disabled="view.isStructureLocked.value" class="contents">
        <OSObjetoTab
          v-if="activeTab === 'objeto'"
          v-model="objetoModel"
          :objeto-dados="view.objetoDados.value"
          :os-dados="view.osDados.value"
          :objetos-historico="view.objetosHistorico.value"
          :selected-historico="view.selectedHistorico.value"
          :is-locked="view.isStructureLocked.value"
          :is-create-mode="view.isCreateMode.value"
          :errors="view.formErrors.value"
          @update:objeto-dados="view.setObjetoDados"
          @update:os-dados="view.setOsDados"
          @update:selected-historico="view.setSelectedHistorico"
          @apply-historico="view.applyObjetoHistorico"
        />

        <OSVistoriaTab
          v-if="activeTab === 'vistoria'"
          :os-dados="view.osDados.value"
          :is-locked="view.isStructureLocked.value"
          @update:os-dados="view.setOsDados"
          @imprimir-ficha-entrada="view.imprimirFicha('ENTRADA')"
          @imprimir-ficha-saida="view.imprimirFicha('SAIDA')"
        />

        <OSServicesTab
          v-if="activeTab === 'servicos'"
          :itens="view.displayItems.value"
          :is-locked="view.isItemsLocked.value"
          @add-item="view.openAddItemModal"
          @edit-item="view.openEditItemModal"
          @remove-item="view.handleRemoveItem"
        />
      </fieldset>

      <OSDiagnosticoTab
        v-if="activeTab === 'diagnostico'"
        :diagnostico="view.currentDiagnostico.value"
        :os-numero="view.currentOSData.value?.numero_os"
        :fotos="view.currentOSData.value?.fotos ?? []"
        :pending-photos="view.pendingPhotos.value"
        :is-locked="view.isDiagnosticoLocked.value"
        @update:diagnostico="view.handleDiagnosticoUpdate"
        @add-photo="view.handleAddPhoto"
        @remove-pending="view.handleRemovePending"
        @photo-change="view.handlePhotoChange"
      />
    </div>
  </div>
</template>
