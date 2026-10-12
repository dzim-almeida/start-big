<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import OSFormHeader from './OSFormHeader.vue';
import OSFormFooter from './OSFormFooter.vue';
import OSFormSidebar from './OSFormSidebar.vue';
import OSControlsCard from './OSControlsCard.vue';
import OSFormTabsContent from './OSFormTabsContent.vue';
import { useOSFormView } from '../../context/useOSFormView.context';
import { useAuthStore } from '@/shared/stores/auth.store';
import { computed, defineAsyncComponent, watch } from 'vue';
import { useRouter } from 'vue-router';

import BaseSectionCard from '@/shared/components/layout/SectionCard/BaseSectionCard.vue';
import BaseStepper from '@/shared/components/ui/BaseStepper/BaseStepper.vue';
import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { useRotulosStatusOS } from '@/modules/order-service/shared/segmento/useRotulosStatusOS';
import { etapasDaOS } from '@/modules/marcenaria/os/utils/etapasOS';
import type { OsStatusEnumDataType } from '../../schemas/enums/osEnums.schema';

// Marcenaria (redesign 10/2026): cabeçalho e rodapé próprios, sob demanda —
// os outros segmentos nem baixam.
const OSMarcenariaCabecalho = defineAsyncComponent(() => import('@/modules/marcenaria/os/components/OSMarcenariaCabecalho.vue'));
const OSMarcenariaRodape = defineAsyncComponent(() => import('@/modules/marcenaria/os/components/OSMarcenariaRodape.vue'));

const view = useOSFormView();
const authStore = useAuthStore();
const router = useRouter();

/**
 * Marcenaria numa OS que já existe: tela cheia, abas sublinhadas, a coluna
 * lateral só na Visão Geral e o rodapé com total, sinal e "Avançar". A
 * criação (rara: a OS nasce do orçamento) e os outros segmentos: como sempre.
 */
const { temOrcamentoTecnico } = useCapacidades();
const marcenaria = computed(() => temOrcamentoTecnico.value && !view.isCreateMode.value);

/** Rótulo de um status no vocabulário do segmento ("Em Produção"); o único lugar que sabe disso. */
const { rotuloStatus: rotuloDoSegmento } = useRotulosStatusOS();
const rotuloStatus = (status: string) => rotuloDoSegmento(status as OsStatusEnumDataType);
const etapas = computed(() => etapasDaOS(view.controlsStatus.value, rotuloStatus));

/** "Origem: Orçamento ORC-…" no cabeçalho: fecha a OS e abre o orçamento. */
function abrirOrcamento(id: number) {
  view.handleClose();
  void router.push({ name: 'marcenaria-orcamento', params: { id } });
}

const avancarStatus = (status: string) => view.aplicarStatusSalvo(status as OsStatusEnumDataType);

const canSelectTecnico = computed(() => {
  const user = authStore.userData;
  if (!user) return false;
  if (!user.cargo) return false;
  const p = user.cargo.permissoes;
  return p?.['all'] === true || p?.['funcionario'] === true;
});

watch(
  () => authStore.userData?.funcionario_id,
  (funcionarioId) => {
    if (!canSelectTecnico.value && funcionarioId) {
      view.handleFuncionarioIdUpdate(String(funcionarioId));
    }
  },
  { immediate: true },
);
</script>

<template>
  <BaseModal :is-open="view.isOpen.value" title="" :size="marcenaria ? 'full' : '4xl'" @close="view.handleClose">
    <template #header>
      <OSMarcenariaCabecalho
        v-if="marcenaria"
        :numero-os="view.currentOSData.value?.numero_os ?? null"
        :rotulo-status="rotuloStatus(view.controlsStatus.value)"
        :status="view.controlsStatus.value"
        :prioridade="view.controlsPrioridade.value"
        :projeto="view.currentOSData.value?.objeto?.numero_serie ?? null"
        :data-criacao="view.currentOSData.value?.data_criacao ?? null"
        @close="view.handleClose"
        @abrir-orcamento="abrirOrcamento"
      />
      <OSFormHeader
        v-else
        :os-number="view.currentOSData.value?.numero_os ?? '...'"
        :is-finalizada="view.isFinalizada.value"
        :is-cancelada="view.isCancelada.value"
        :is-create-mode="view.isCreateMode.value"
        @close="view.handleClose"
      />
    </template>

    <form class="space-y-4" @submit.prevent="view.handleLocalSubmit">
      <!-- Marcenaria: os controles e a lateral entram na Visão Geral (slots das abas). -->
      <OSFormTabsContent v-if="marcenaria">
        <template #visao-geral>
          <BaseSectionCard titulo="Etapas da OS" descricao="Avançam ao trocar a situação">
            <BaseStepper :etapas="etapas" />
          </BaseSectionCard>
          <OSControlsCard
            :status="view.controlsStatus.value"
            :is-create-mode="view.isCreateMode.value"
            :funcionario-id="view.controlsFuncionarioId.value"
            :prioridade="view.controlsPrioridade.value"
            :data-previsao="view.controlsDataPrevisao.value"
            :status-options="view.statusOptions.value"
            :prioridade-options="view.prioridadeOptions.value"
            :funcionarios-options="view.funcionariosOptions.value"
            :errors="view.formErrors.value"
            :can-select-tecnico="canSelectTecnico"
            :is-locked="view.isStructureLocked.value"
            @update:status="view.handleStatusUpdate"
            @update:funcionario-id="view.handleFuncionarioIdUpdate"
            @update:prioridade="view.handlePrioridadeUpdate"
            @update:data-previsao="view.handleDataPrevisaoUpdate"
          />
        </template>
        <template #lateral>
          <OSFormSidebar />
        </template>
      </OSFormTabsContent>

      <template v-else>
        <!-- Status Bar Operacional -->
        <OSControlsCard
          :status="view.controlsStatus.value"
          :is-create-mode="view.isCreateMode.value"
          :funcionario-id="view.controlsFuncionarioId.value"
          :prioridade="view.controlsPrioridade.value"
          :data-previsao="view.controlsDataPrevisao.value"
          :status-options="view.statusOptions.value"
          :prioridade-options="view.prioridadeOptions.value"
          :funcionarios-options="view.funcionariosOptions.value"
          :errors="view.formErrors.value"
          :can-select-tecnico="canSelectTecnico"
          :is-locked="view.isStructureLocked.value"
          @update:status="view.handleStatusUpdate"
          @update:funcionario-id="view.handleFuncionarioIdUpdate"
          @update:prioridade="view.handlePrioridadeUpdate"
          @update:data-previsao="view.handleDataPrevisaoUpdate"
        />

        <div class="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-5 items-start">
          <OSFormTabsContent />
          <OSFormSidebar />
        </div>
      </template>
    </form>

    <template #footer>
      <OSMarcenariaRodape
        v-if="marcenaria"
        :numero-os="view.currentOSData.value?.numero_os ?? null"
        :total-centavos="view.displayValorTotal.value"
        :status="view.controlsStatus.value"
        :rotulo="rotuloStatus"
        :travada="view.isStructureLocked.value"
        :avancar="avancarStatus"
      >
        <OSFormFooter
          :is-finalizada="view.isFinalizada.value"
          :is-cancelada="view.isCancelada.value"
          :is-edit-mode="view.isEditMode.value"
          :is-create-mode="view.isCreateMode.value"
          :is-pending="view.isPending.value"
          :reopen-mode="view.reopenMode.value"
          :os-id="view.currentOSData.value?.id"
          @finalizar="view.handleFinalizarOS"
          @print="view.printEntrada"
          @reprint-exit="view.printSaida"
          @reopen="view.handleReopenClick"
          @save="view.handleLocalSubmit"
        />
      </OSMarcenariaRodape>
      <OSFormFooter
        v-else
        :is-finalizada="view.isFinalizada.value"
        :is-cancelada="view.isCancelada.value"
        :is-edit-mode="view.isEditMode.value"
        :is-create-mode="view.isCreateMode.value"
        :is-pending="view.isPending.value"
        :reopen-mode="view.reopenMode.value"
        :os-id="view.currentOSData.value?.id"
        @finalizar="view.handleFinalizarOS"
        @print="view.printEntrada"
        @reprint-exit="view.printSaida"
        @reopen="view.handleReopenClick"
        @save="view.handleLocalSubmit"
      />
    </template>
  </BaseModal>
</template>
