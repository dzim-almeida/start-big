<script setup lang="ts">
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import OSFormHeader from './OSFormHeader.vue';
import OSFormFooter from './OSFormFooter.vue';
import OSFormSidebar from './OSFormSidebar.vue';
import OSFormTabsContent from './OSFormTabsContent.vue';
import { useOSFormView } from '../../context/useOSFormView.context';

const view = useOSFormView();
</script>

<template>
  <BaseModal :is-open="view.isOpen.value" title="" size="4xl" @close="view.handleClose">
    <template #header>
      <OSFormHeader
        :os-number="view.currentOSData.value?.numero_os ?? '...'"
        :is-finalizada="view.isFinalizada.value"
        :is-cancelada="view.isCancelada.value"
        :is-create-mode="view.isCreateMode.value"
        @close="view.handleClose"
      />
    </template>

    <form class="space-y-4" @submit.prevent="view.handleLocalSubmit">
      <div class="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-5 items-start">
        <OSFormSidebar />
        <OSFormTabsContent />
      </div>
    </form>

    <template #footer>
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
    </template>
  </BaseModal>
</template>
