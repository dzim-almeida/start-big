<script setup lang="ts">
import { Plus, AlertTriangle } from 'lucide-vue-next';
import { useMagicKeys, whenever } from '@vueuse/core';

import { useToast } from '@/shared/composables/useToast';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import ConfirmationTemplate from '@/shared/components/templates/ConfirmationTemplate.vue';

import SalesStatus from './components/SalesStatus.vue';
import SaleTable from './components/SaleTable.vue';
import SaleModal from './components/SaleModal.vue';
import CustomerSearchModal from './components/CustomerSearchModal.vue';

import { useCustomerSearchModal } from './composables/flows/useCustomerSearchModal';
import { useSaleModal } from './composables/flows/useSaleModal';
import { useFinishSaleModal } from './composables/flows/useFinishSaleModal';
import { useConfirmSaleAction } from './composables/flows/useConfirmSaleAction';
import { useCancelSaleMutation } from './composables/mutates/useCancelSaleMutation';
import { useReopenSaleMutation } from './composables/mutates/useReopenSaleMutation';

const toast = useToast();

const { openCustomerModal } = useCustomerSearchModal();
const { openSaleEditModal, saleModalIsOpen } = useSaleModal();
const { openFinishModal } = useFinishSaleModal();

const { F2 } = useMagicKeys();
whenever(F2, () => {
  if (!saleModalIsOpen.value) {
    openCustomerModal();
  }
});

const {
  confirmModalIsOpen,
  confirmModalState,
  confirmModalPending,
  openConfirmModal,
  closeConfirmModal,
  handleConfirm,
} = useConfirmSaleAction();

const cancelMutation = useCancelSaleMutation();
const reopenMutation = useReopenSaleMutation();

function handleFinishFromTable(saleId: number) {
  openSaleEditModal(saleId);
  setTimeout(() => openFinishModal(), 300);
}

function handleCancelFromTable(saleId: number) {
  openConfirmModal({
    title: 'Cancelar Venda?',
    message: 'Tem certeza que deseja cancelar a Venda',
    highlightText: `Nº ${String(saleId).padStart(6, '0')}`,
    variant: 'danger',
    label: 'CONFIRMAR',
    action: () => {
      confirmModalPending.value = true;
      cancelMutation.mutate(
        { saleId },
        {
          onSuccess: () => closeConfirmModal(),
          onSettled: () => { confirmModalPending.value = false; },
        },
      );
    },
  });
}

function handleReopenFromTable(saleId: number) {
  openConfirmModal({
    title: 'Reabrir Venda?',
    message: 'Deseja reabrir a Venda',
    highlightText: `Nº ${String(saleId).padStart(6, '0')}`,
    variant: 'primary',
    label: 'CONFIRMAR',
    action: () => {
      confirmModalPending.value = true;
      reopenMutation.mutate(
        { saleId },
        {
          onSuccess: () => closeConfirmModal(),
          onSettled: () => { confirmModalPending.value = false; },
        },
      );
    },
  });
}

function handlePrintFromTable(_saleId: number) {
  toast.info('Impressão em breve', 'Funcionalidade de impressão será implementada em breve.');
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview title="Vendas" description="Gerencie as vendas do seu estabelecimento." />
      <BaseButton
        variant="primary"
        size="md"
        type="button"
        class="flex gap-1"
        @click="openCustomerModal"
      >
        <Plus :size="20" />
        Nova venda
      </BaseButton>
    </div>

    <SalesStatus />
    <SaleTable
      @cancel="handleCancelFromTable"
      @finish="handleFinishFromTable"
      @reopen="handleReopenFromTable"
      @print="handlePrintFromTable"
    />

    <CustomerSearchModal />
    <SaleModal />

    <BaseModal
      :is-open="confirmModalIsOpen"
      :title="confirmModalState.title"
      size="sm"
      @close="closeConfirmModal"
    >
      <ConfirmationTemplate
        :icon="AlertTriangle"
        icon-bg-class="bg-brand-primary-light"
        icon-color-class="text-brand-primary"
      >
        <template #description>
          <p class="text-sm text-slate-500 leading-relaxed">
            {{ confirmModalState.message }}
            <span v-if="confirmModalState.highlightText" class="font-bold text-slate-800 block mt-1 text-base">
              {{ confirmModalState.highlightText }}
            </span>
          </p>
        </template>

        <template #footer>
          <div class="flex gap-3 w-full mt-6">
            <BaseButton
              variant="secondary"
              class="flex-1"
              :disabled="confirmModalPending"
              @click="closeConfirmModal"
            >
              VOLTAR
            </BaseButton>
            <BaseButton
              :variant="confirmModalState.variant"
              :is-loading="confirmModalPending"
              class="flex-1"
              @click="handleConfirm"
            >
              {{ confirmModalState.label }}
            </BaseButton>
          </div>
        </template>
      </ConfirmationTemplate>
    </BaseModal>
  </div>
</template>