<script setup lang="ts">
import { computed, nextTick } from 'vue';
import { X } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import ProductSearch from './SaleModal/ProductSearch.vue';
import CustomerCard from './SaleModal/CustomerCard.vue';
import SaleCard from './SaleModal/SaleCard.vue';
import SaleItemsTable from './SaleModal/SaleItemsTable.vue';
import SaleSummary from './SaleModal/SaleSummary.vue';
import ItemModal from './SaleModal/ItemModal.vue';
import FinishSaleModal from './SaleModal/FinishSaleModal.vue';

import { SALE_FILTERS, STATUS_COLORS } from '../constants';

import { useFinishSaleModal } from '../composables/flows/useFinishSaleModal';
import { useSaleModal } from '../composables/flows/useSaleModal';
import { useItemModal } from '../composables/flows/useItemModal';
import { useConfirmSaleAction } from '../composables/flows/useConfirmSaleAction';
import { useCancelSaleMutation } from '../composables/mutates/useCancelSaleMutation';
import { useUpdateSaleMutation } from '../composables/mutates/useUpdateSaleMutation';
import { useCustomerSearchModal } from '../composables/flows/useCustomerSearchModal';
import { useSaleShortcuts } from '../composables/useSaleShortcuts';

const { saleModalIsOpen, closeSaleModal, sale, selectedSaleId, isEditMode, isViewMode } = useSaleModal();
const { openFinishModal, closeFinishModal, finishModalIsOpen, addPaymentModalIsOpen, openAddPaymentModal, closeAddPaymentModal } = useFinishSaleModal();
const { itemModalIsOpen, openCreateItemModal, closeItemModal } = useItemModal();
const { openConfirmModal, closeConfirmModal: closeConfirm, confirmModalPending } = useConfirmSaleAction();
const cancelMutation = useCancelSaleMutation();
const updateSaleMutation = useUpdateSaleMutation();
const { openCustomerModalForChange } = useCustomerSearchModal();

function handleChangeCliente() {
  if (!sale.value) return;
  const saleId = sale.value.id;

  openCustomerModalForChange((clienteId) => {
    updateSaleMutation.mutate({
      saleId,
      payload: { cliente_id: clienteId },
    });
  });
}

function handleCancel() {
  if (!sale.value) return;

  const saleId = sale.value.id;
  const displayNumber = String(saleId).padStart(6, '0');

  openConfirmModal({
    title: 'Cancelar Venda?',
    message: 'Tem certeza que deseja cancelar a Venda',
    highlightText: `Nº ${displayNumber}`,
    variant: 'danger',
    label: 'CONFIRMAR',
    action: () => {
      confirmModalPending.value = true;
      cancelMutation.mutate(
        { saleId },
        {
          onSuccess: () => {
            closeConfirm();
            closeSaleModal();
          },
          onSettled: () => { confirmModalPending.value = false; },
        },
      );
    },
  });
}

useSaleShortcuts({
  saleModalIsOpen,
  isEditMode,
  finishModalIsOpen,
  itemModalIsOpen,
  addPaymentModalIsOpen,
  onCreateSale: () => {},
  onOpenFinishModal: openFinishModal,
  onOpenItemModal: openCreateItemModal,
  onOpenAddPaymentModal: openAddPaymentModal,
  onCancelSale: handleCancel,
  onCloseSaleModal: closeSaleModal,
  onCloseFinishModal: closeFinishModal,
  onCloseItemModal: closeItemModal,
  onCloseAddPaymentModal: closeAddPaymentModal,
  onFocusSearch: () => {
    nextTick(() => {
      const searchInput = document.querySelector<HTMLInputElement>('[data-search-products] input');
      searchInput?.focus();
    });
  },
});

const orcamentoDisplay = computed(() => {
  if (!sale.value) return '...';
  return `Orçamento #${String(sale.value.id).padStart(6, '0')}`;
});

const vendaDisplay = computed(() => {
  if (!sale.value?.numero_venda) return null;
  return `Venda #${String(sale.value.numero_venda).padStart(6, '0')}`;
});
</script>

<template>
  <BaseModal
    :is-open="saleModalIsOpen"
    :title="orcamentoDisplay"
    subtitle="Gerencie os detalhes desta venda, adicione produtos, finalize ou cancele a venda"
    size="4xl"
    @close="closeSaleModal"
  >
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-zinc-800">
            {{ orcamentoDisplay }}
          </h2>
          <span v-if="vendaDisplay" class="text-sm font-medium text-green-700">
            {{ vendaDisplay }}
          </span>
          <span
            :class="[
              'px-2 py-0.5 text-xs font-medium rounded-full',
              STATUS_COLORS[sale?.status!].text,
              STATUS_COLORS[sale?.status!].bg,
            ]"
          >
            {{ SALE_FILTERS[sale?.status!].label }}
          </span>
        </div>

        <button
          type="button"
          class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          @click="closeSaleModal()"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <main class="w-full min-h-[80vh] flex flex-wrap md:flex-nowrap gap-4 border-red-500">
      <section class="w-full md:w-2/3 flex flex-col gap-5">
        <ProductSearch v-if="isEditMode" :sale-id="selectedSaleId"/>
        <SaleItemsTable :sale="sale" :readonly="isViewMode"/>
        <SaleSummary :subtotal="sale?.subtotal"  :discount="sale?.descontos" :delivery="sale?.entrega" :total="sale?.total"/>
      </section>
      <section class="w-full md:w-1/3 flex flex-col gap-4">
        <CustomerCard :customer="sale?.cliente" :readonly="isViewMode" @change-cliente="handleChangeCliente" />
        <SaleCard :sale="sale" :readonly="isViewMode" />
        <div v-if="isEditMode" class="mt-auto flex justify-around gap-5 w-full">
          <BaseButton variant="danger" size="md" class="flex-1" @click="handleCancel">
            Cancelar Venda
          </BaseButton>
          <BaseButton variant="primary" size="md" class="flex-1" @click="openFinishModal">
            Finalizar
          </BaseButton>
        </div>
        <div v-else class="mt-auto flex justify-center w-full">
          <BaseButton variant="secondary" size="md" class="flex-1" @click="closeSaleModal()">
            Fechar
          </BaseButton>
        </div>
      </section>
    </main>
    <ItemModal :sale-id="selectedSaleId" />
    <FinishSaleModal :sale="sale" />
  </BaseModal>
</template>
