<script setup lang="ts">
import { computed, nextTick } from 'vue';
import { X, Printer, ShoppingCart } from 'lucide-vue-next';
import { useAuthStore } from '@/shared/stores/auth.store';

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
import { useSalePrintFlow } from '../composables/flows/useSalePrintFlow';
import type { SaleRead } from '../schemas/sale.schema';

import PrintFormatSelectModal from '@/shared/components/print/PrintFormatSelectModal.vue';
import SalePrintTemplate from './print/SalePrintTemplate.vue';
import SalePrintCupom from './print/SalePrintCupom.vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const authStore = useAuthStore();
const logoUrl = computed(() => {
  const path = authStore.userData?.empresa?.url_logo;
  if (!path) return null;
  return `${API_BASE_URL}/${path}`;
});

const { saleModalIsOpen, closeSaleModal, sale, selectedSaleId, isEditMode, isViewMode } = useSaleModal();
const { openFinishModal, closeFinishModal, finishModalIsOpen } = useFinishSaleModal();
const { itemModalIsOpen, openCreateItemModal, closeItemModal } = useItemModal();
const { openConfirmModal, closeConfirmModal: closeConfirm, confirmModalPending } = useConfirmSaleAction();
const cancelMutation = useCancelSaleMutation();
const updateSaleMutation = useUpdateSaleMutation();
const { openCustomerModalForChange } = useCustomerSearchModal();

const {
  saleForPrint,
  printType,
  printFormat,
  isPrintSelectModalOpen,
  printSaleData,
  handlePrintFormatSelected,
  closePrintSelectModal,
  resolvePaymentMethodName,
} = useSalePrintFlow();

function handleFinalized(finishedSale: SaleRead) {
  printSaleData(finishedSale, 'VENDA', () => closeSaleModal());
}

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

function handlePrint() {
  if (!sale.value) return;
  printSaleData(sale.value, 'VENDA');
}

useSaleShortcuts({
  saleModalIsOpen,
  isEditMode,
  finishModalIsOpen,
  itemModalIsOpen,
  onCreateSale: () => {},
  onOpenFinishModal: openFinishModal,
  onOpenItemModal: openCreateItemModal,
  onFocusPaymentGrid: () => {
    nextTick(() => {
      const btn = document.querySelector<HTMLButtonElement>('[data-payment-grid] button');
      btn?.focus();
    });
  },
  onCancelSale: handleCancel,
  onCloseSaleModal: closeSaleModal,
  onCloseFinishModal: closeFinishModal,
  onCloseItemModal: closeItemModal,
  onFocusSearch: () => {
    nextTick(() => {
      const searchInput = document.querySelector<HTMLInputElement>('[data-search-products] input');
      searchInput?.focus();
    });
  },
  onFocusSaleInputs: (field) => {
    nextTick(() => {
      document.querySelector<HTMLInputElement>(`[data-sale-${field}] input`)?.focus();
    });
  },
});

const saleDisplay = computed(() => {
  if (!sale.value) return '...';
  return `Venda #${String(sale.value.id).padStart(6, '0')}`;
});
</script>

<template>
  <BaseModal
    :is-open="saleModalIsOpen"
    :title="saleDisplay"
    subtitle="Gerencie os detalhes desta venda, adicione produtos, finalize ou cancele a venda"
    size="4xl"
    @close="closeSaleModal"
  >
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" :class="logoUrl ? '' : 'bg-brand-primary'">
            <img v-if="logoUrl" :src="logoUrl" alt="Logo" class="w-full h-full object-cover rounded-lg" />
            <ShoppingCart v-else :size="18" class="text-white" />
          </div>
          <h2 class="text-xl font-bold text-zinc-800">
            {{ saleDisplay }}
          </h2>
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

        <div class="flex items-center gap-1">
          <button
            type="button"
            class="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors cursor-pointer"
            title="Imprimir"
            @click="handlePrint"
          >
            <Printer :size="18" />
          </button>
          <button
            type="button"
            class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
            @click="closeSaleModal()"
          >
            <X :size="20" />
          </button>
        </div>
      </div>
    </template>

    <main class="w-full min-h-[80vh] flex flex-wrap md:flex-nowrap gap-4">
      <section class="w-full md:w-2/3 flex flex-col gap-5">
        <ProductSearch v-if="isEditMode" :sale-id="selectedSaleId" :current-items="sale?.produtos" />
        <SaleItemsTable :sale="sale" :readonly="isViewMode"/>
        <SaleSummary :subtotal="sale?.subtotal"  :discount="sale?.descontos" :delivery="sale?.entrega" :total="sale?.total"/>
      </section>
      <section class="w-full md:w-1/3 flex flex-col min-h-0 max-h-[80vh]">
        <div class="flex-1 overflow-y-scroll flex flex-col gap-4 pr-1">
          <CustomerCard :customer="sale?.cliente" :readonly="isViewMode" @change-cliente="handleChangeCliente" />
          <SaleCard :sale="sale" :readonly="isViewMode" />
        </div>
        <div class="shrink-0 pt-4">
          <div v-if="isEditMode" class="flex justify-around gap-5 w-full">
            <BaseButton variant="danger" size="md" class="flex-1" @click="handleCancel">
              <div class="flex flex-col items-center">
                <span>Cancelar Orçamento</span>
                <span class="text-[9px] opacity-70 font-normal">Ctrl+Backspace</span>
              </div>
            </BaseButton>
            <BaseButton variant="primary" size="md" class="flex-1" :disabled="!sale?.produtos?.length" @click="openFinishModal">
              <div class="flex flex-col items-center">
                <span>Finalizar</span>
                <span class="text-[9px] opacity-70 font-normal">Ctrl+Enter</span>
              </div>
            </BaseButton>
          </div>
          <div v-else class="flex justify-center w-full">
            <BaseButton variant="secondary" size="md" class="flex-1" @click="closeSaleModal()">
              Fechar
            </BaseButton>
          </div>
        </div>
      </section>

    </main>
    <ItemModal :sale-id="selectedSaleId" />
    <FinishSaleModal :sale="sale" @finalized="handleFinalized" />

    <!-- Print Infrastructure -->
    <PrintFormatSelectModal
      :is-open="isPrintSelectModalOpen"
      subtitle="Selecione o formato para impressão da venda."
      @close="closePrintSelectModal"
      @select="handlePrintFormatSelected"
    />

    <SalePrintTemplate
      v-if="saleForPrint && printFormat === 'A4'"
      :sale="saleForPrint"
      :type="(printType as 'VENDA')"
      :payment-method-resolver="resolvePaymentMethodName"
    />

    <SalePrintCupom
      v-if="saleForPrint && printFormat === 'CUPOM'"
      :sale="saleForPrint"
      :type="(printType as 'VENDA')"
      :payment-method-resolver="resolvePaymentMethodName"
    />
  </BaseModal>
</template>
