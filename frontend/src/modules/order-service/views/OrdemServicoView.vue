<script setup lang="ts">
import { ref, computed } from 'vue';
import { Plus } from 'lucide-vue-next';

import { TAB_OPTIONS } from '../ordens/constants/ordemServico.constants';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTab2 from '@/shared/components/ui/BaseTab2/BaseTab2.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import OrdensServicoTab from './tabs/OrdensServicoTab.vue';
import ServicosTab from './tabs/ServicosTab.vue';

import { useServicoModal } from '../servicos/composables/useServicoModal';

const { openCreateModal } = useServicoModal();

const activeTab = ref('ordens');
const ordensTabRef = ref<InstanceType<typeof OrdensServicoTab> | null>(null);

const pageTitle = computed(() =>
  activeTab.value === 'ordens' ? 'Ordens de Serviço' : 'Cadastro de Serviços',
);

const pageDescription = computed(() =>
  activeTab.value === 'ordens'
    ? 'Gerencie as ordens de serviço da sua assistência.'
    : 'Gerencie o catálogo de serviços da sua organização.',
);

function handleAddClick() {
  if (activeTab.value === 'ordens') {
    ordensTabRef.value?.handleOpenNovaOS();
  } else {
    openCreateModal();
  }
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        :title="pageTitle"
        :description="pageDescription"
      />

      <div class="flex gap-5">
        <BaseTab2 :options="TAB_OPTIONS" v-model="activeTab" />
        <BaseButton
          variant="primary"
          size="md"
          type="button"
          class="flex gap-1"
          @click="handleAddClick"
        >
          <Plus :size="20" />
          {{ activeTab === 'ordens' ? 'Nova OS' : 'Novo Serviço' }}
        </BaseButton>
      </div>
    </div>

    <template v-if="activeTab === 'ordens'">
      <OrdensServicoTab ref="ordensTabRef" />
    </template>

    <template v-else>
      <ServicosTab />
    </template>
  </div>
</template>
