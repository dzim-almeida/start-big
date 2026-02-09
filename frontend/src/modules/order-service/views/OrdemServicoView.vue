<script setup lang="ts">
import { Plus } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import ServicosTab from './tabs/ServicosTab.vue';
import { useServicoModal } from '../composables/useServicoModal';

const { openCreateModal } = useServicoModal();
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        title="Serviços"
        description="Gerencie o catálogo de serviços da sua organização."
      />

      <BaseButton
        variant="primary"
        size="md"
        type="button"
        class="flex gap-1"
        @click="openCreateModal"
      >
        <Plus :size="20" />
        Adicionar Serviço
      </BaseButton>
    </div>

    <ServicosTab />
  </div>
</template>
