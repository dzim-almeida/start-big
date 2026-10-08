<script setup lang="ts">
import { ref, computed, watch, defineAsyncComponent, type Component } from 'vue';
import { ClipboardCheck, ClipboardList, Image as ImageIcon, Package, Ruler } from 'lucide-vue-next';

import OSObjetoTab from './OSObjetoTab.vue';
import OSObjetoDinamicoTab from './OSObjetoDinamicoTab.vue';
import OSVistoriaTab from './OSVistoriaTab.vue';
import OSDiagnosticoTab from './OSDiagnosticoTab.vue';
import OSServicesTab from './OSServicesTab.vue';
import type { ObjetoFormData } from '../../composables/modal/useOSFormAdapter';
import { useOSFormView } from '../../context/useOSFormView.context';
import { useObjetoLabels } from '@/modules/order-service/shared/segmento/useObjetoLabels';
import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { useTiposDeTrabalho } from '@/modules/order-service/shared/segmento/useTiposDeTrabalho';
import { useAcessoCompras } from '@/modules/compras/shared/composables/useAcessoCompras';

// Módulo Compras (fase 6): "Compras desta OS" na aba de peças. Só com o módulo
// e a permissão, e carregado sob demanda — quem não tem Compras nem baixa.
const { podeVer: comprasDisponivel } = useAcessoCompras();
const ComprasDaOSPanel = defineAsyncComponent(
  () => import('@/modules/compras/ordens-servico/components/ComprasDaOSPanel.vue'),
);
const osSalvaId = computed(() => view.currentOSData.value?.id ?? null);

// Marcenaria-fábrica: a aba Orçamento só existe na OS que nasceu no trilho
// (`fase_fabrica` preenchida). Sob demanda — os outros segmentos nem baixam.
const OrcamentoFabricaTab = defineAsyncComponent(
  () => import('@/modules/order-service/fabrica/components/OrcamentoFabricaTab.vue'),
);
const ehDaFabrica = computed(() => !!view.currentOSData.value?.fase_fabrica);
const TrilhoFabrica = defineAsyncComponent(
  () => import('@/modules/order-service/fabrica/components/TrilhoFabrica.vue'),
);
const clienteDaOS = computed(() => {
  const cliente = view.currentOSData.value?.cliente as { nome?: string; razao_social?: string; nome_fantasia?: string } | undefined;
  return cliente?.nome ?? cliente?.nome_fantasia ?? cliente?.razao_social ?? '';
});

type TabType = 'objeto' | 'vistoria' | 'diagnostico' | 'servicos' | 'orcamento';

const view = useOSFormView();

// Rótulo e ícone da aba do objeto vêm do contrato (Veículo/Equipamento).
const { labelSingular, objetoIcon } = useObjetoLabels();
const { temVistoria, temDiagnostico, temImagemNaEntrada } = useCapacidades();

// Qual aba de objeto usar. `temTipos` só é verdadeiro para segmento que declara
// tipos de trabalho no registry — oficina e informática não declaram, então
// continuam na tab curada, pelo mesmo caminho de sempre.
const { temTipos } = useTiposDeTrabalho();

const activeTab = ref<TabType>('objeto');

watch(() => view.isOpen.value, (open) => {
  if (open) {
    activeTab.value = 'objeto';
  }
});

const allTabs = computed<{ id: TabType; label: string; icon: Component }[]>(() => {
  const tabs: { id: TabType; label: string; icon: Component }[] = [
    { id: 'objeto', label: labelSingular.value, icon: objetoIcon.value },
  ];
  // Vistoria: só para segmentos que declaram a capacidade no registry.
  if (temVistoria.value) {
    tabs.push({ id: 'vistoria', label: 'Vistoria', icon: ClipboardCheck });
  }
  tabs.push(
    // Sem diagnóstico a aba não some: ela guarda a galeria de fotos, e em
    // serigrafia a foto É a arte que o cliente aprova pelo celular. Muda só o
    // nome, para não prometer laudo onde não há o que laudar.
    temDiagnostico.value
      ? { id: 'diagnostico', label: 'Diagnóstico', icon: ClipboardList }
      : { id: 'diagnostico', label: 'Imagens', icon: ImageIcon },
    { id: 'servicos', label: 'Serviços e Peças', icon: Package },
  );
  if (ehDaFabrica.value) {
    tabs.push({ id: 'orcamento', label: 'Orçamento', icon: Ruler });
  }
  return tabs;
});

/**
 * Na criação a aba de imagens some — a foto de oficina/informática é prova do
 * estado do bem e nasce depois, com o aparelho na bancada.
 *
 * Onde a imagem é o PEDIDO (serigrafia: a foto é a arte a estampar), ela precisa
 * entrar já no primeiro cadastro. Quem decide é a capacidade do registry, não o
 * nome do segmento — as fotos ficam pendentes em memória e sobem assim que a OS
 * nasce (useOSPendingPhotos).
 */
const visibleTabs = computed(() => {
  const escondeImagens = view.isCreateMode.value && !temImagemNaEntrada.value;
  return escondeImagens
    ? allTabs.value.filter((tab) => tab.id !== 'diagnostico')
    : allTabs.value;
});

const objetoModel = computed<ObjetoFormData>({
  get: () => view.objetoFormData.value,
  set: (value) => view.setObjetoFormData(value),
});
</script>

<template>
  <div>
    <TrilhoFabrica
      v-if="ehDaFabrica && view.currentOSData.value"
      :numero-os="view.currentOSData.value.numero_os"
      :fase="view.currentOSData.value.fase_fabrica ?? ''"
      :atualizado-em="view.currentOSData.value.data_atualizacao"
      class="mb-4"
      @os-alterada="view.refreshCurrentOSData"
    />
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
        <OSObjetoDinamicoTab
          v-if="activeTab === 'objeto' && temTipos"
          v-model="objetoModel"
          :objeto-dados="view.objetoDados.value"
          :os-dados="view.osDados.value"
          :errors="view.formErrors.value"
          :is-locked="view.isStructureLocked.value"
          :is-create-mode="view.isCreateMode.value"
          :objetos-historico="view.objetosHistorico.value"
          :selected-historico="view.selectedHistorico.value"
          @update:objeto-dados="view.setObjetoDados"
          @update:os-dados="view.setOsDados"
          @update:selected-historico="view.setSelectedHistorico"
          @apply-historico="view.applyObjetoHistorico"
        />

        <OSObjetoTab
          v-else-if="activeTab === 'objeto'"
          v-model="objetoModel"
          :objeto-dados="view.objetoDados.value"
          :os-dados="view.osDados.value"
          :objetos-historico="view.objetosHistorico.value"
          :selected-historico="view.selectedHistorico.value"
          :is-locked="view.isStructureLocked.value"
          :is-create-mode="view.isCreateMode.value"
          :errors="view.formErrors.value"
          :cliente-id="view.currentCliente.value?.id ?? null"
          @update:objeto-dados="view.setObjetoDados"
          @update:os-dados="view.setOsDados"
          @update:selected-historico="view.setSelectedHistorico"
          @apply-historico="view.applyObjetoHistorico"
          @abrir-com-cliente="view.handleAbrirComCliente"
        />

        <OSVistoriaTab
          v-if="activeTab === 'vistoria'"
          :os-dados="view.osDados.value"
          :os-dados-persistido="view.currentOSData.value?.dados_adicionais ?? {}"
          :is-locked="view.isStructureLocked.value"
          :os-number="view.currentOSData.value?.numero_os ?? ''"
          :is-create-mode="view.isCreateMode.value"
          @update:os-dados="view.setOsDados"
          @imprimir-ficha-entrada="view.imprimirFicha('ENTRADA')"
          @imprimir-ficha-saida="view.imprimirFicha('SAIDA')"
          @imprimir-vistoria-preenchida="view.imprimirVistoriaPreenchida()"
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

      <!-- Fora do fieldset: o painel só lê, e não pode travar junto da OS. -->
      <ComprasDaOSPanel
        v-if="activeTab === 'servicos' && comprasDisponivel && osSalvaId"
        :os-id="osSalvaId"
      />

      <!-- Fora do fieldset: tem as próprias ações e travas (só o rascunho se edita). -->
      <OrcamentoFabricaTab
        v-if="activeTab === 'orcamento' && ehDaFabrica && view.currentOSData.value"
        :numero-os="view.currentOSData.value.numero_os"
        :cliente="clienteDaOS"
        :projeto="view.currentOSData.value.objeto?.modelo ?? ''"
        :travada="view.isFinalizada.value || view.isCancelada.value"
        @os-alterada="view.refreshCurrentOSData"
      />

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
