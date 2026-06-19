<script setup lang="ts">
import { computed, nextTick } from 'vue';
import { X, Printer, ShoppingCart } from 'lucide-vue-next';
import { useMagicKeys, whenever, useEventListener } from '@vueuse/core';
import { useAuthStore } from '@/shared/stores/auth.store';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import ProductSearch from './SaleModal/ProductSearch.vue';
import SaleItemsTable from './SaleModal/SaleItemsTable.vue';
import SaleSummary from './SaleModal/SaleSummary.vue';
import ItemModal from './SaleModal/ItemModal.vue';
import OrcamentoCard from './OrcamentoModal/OrcamentoCard.vue';

import { useOrcamentoModal } from '../composables/flows/useOrcamentoModal';
import { useItemModal } from '../composables/flows/useItemModal';
import { useDeleteOrcamentoMutation } from '../composables/mutates/useDeleteOrcamentoMutation';
import { useUpdateOrcamentoMutation } from '../composables/mutates/useUpdateOrcamentoMutation';
import { useConfirmSaleAction } from '../composables/flows/useConfirmSaleAction';
import { getImageUrl } from '@/shared/utils/print.utils';

const emit = defineEmits<{
  (e: 'converter', orcamentoId: number): void;
  (e: 'openSale', saleId: number): void;
  (e: 'print', orcamentoId: number): void;
}>();

const authStore = useAuthStore();
const logoUrl = computed(() => getImageUrl(authStore.userData?.empresa?.url_logo));

const { orcamentoModalIsOpen, closeOrcamentoModal, orcamento, selectedOrcamentoId } = useOrcamentoModal();
const { itemModalIsOpen } = useItemModal();

// Atalhos Ctrl+E (entrega) e Ctrl+D (desconto)
const keys = useMagicKeys();

useEventListener(document, 'keydown', (e: KeyboardEvent) => {
  if (e.ctrlKey && (e.key === 'e' || e.key === 'd') && orcamentoModalIsOpen.value && !orcamento.value?.convertido) {
    e.preventDefault();
  }
});

whenever(keys.Ctrl_E, () => {
  if (orcamentoModalIsOpen.value && !orcamento.value?.convertido && !itemModalIsOpen.value) {
    nextTick(() => document.querySelector<HTMLInputElement>('[data-sale-entrega] input')?.focus());
  }
});

whenever(keys.Ctrl_D, () => {
  if (orcamentoModalIsOpen.value && !orcamento.value?.convertido && !itemModalIsOpen.value) {
    nextTick(() => document.querySelector<HTMLInputElement>('[data-sale-desconto] input')?.focus());
  }
});
const deleteMutation = useDeleteOrcamentoMutation();
const updateMutation = useUpdateOrcamentoMutation();
const { openConfirmModal, closeConfirmModal: closeConfirm, confirmModalPending } = useConfirmSaleAction();

const headerDisplay = computed(() => {
  if (!orcamento.value) return '...';
  return `Orçamento #${String(orcamento.value.id).padStart(6, '0')}`;
});

function handleDelete() {
  if (!orcamento.value) return;

  const orcamentoId = orcamento.value.id;
  const displayNumber = String(orcamentoId).padStart(6, '0');

  openConfirmModal({
    title: 'Excluir Orçamento?',
    message: 'Tem certeza que deseja excluir o Orçamento',
    highlightText: `Nº ${displayNumber}`,
    variant: 'danger',
    label: 'EXCLUIR',
    action: () => {
      confirmModalPending.value = true;
      deleteMutation.mutate(
        { orcamentoId },
        {
          onSuccess: () => {
            closeConfirm();
            closeOrcamentoModal();
          },
          onSettled: () => { confirmModalPending.value = false; },
        },
      );
    },
  });
}

function handleConverter() {
  if (!orcamento.value) return;
  emit('converter', orcamento.value.id);
}

function handleOpenConvertedSale() {
  if (!orcamento.value?.venda_id) return;
  emit('openSale', orcamento.value.venda_id);
}

function handlePrint() {
  if (!orcamento.value) return;
  emit('print', orcamento.value.id);
}
</script>

<template>
  <BaseModal
    :is-open="orcamentoModalIsOpen"
    :title="headerDisplay"
    subtitle="Gerencie os itens deste orçamento"
    size="4xl"
    @close="closeOrcamentoModal"
  >
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" :class="logoUrl ? '' : 'bg-brand-primary'">
            <img v-if="logoUrl" :src="logoUrl" alt="Logo" class="w-full h-full object-cover rounded-lg" />
            <ShoppingCart v-else :size="18" class="text-white" />
          </div>
          <h2 class="text-xl font-bold text-zinc-800">
            {{ headerDisplay }}
          </h2>
          <span
            :class="[
              'px-2 py-0.5 text-xs font-medium rounded-full',
              orcamento?.convertido ? 'text-green-700 bg-green-50' : 'text-blue-700 bg-blue-50',
            ]"
          >
            {{ orcamento?.convertido ? 'Convertido' : 'Ativo' }}
          </span>
          <button
            v-if="orcamento?.convertido && orcamento?.venda_id"
            type="button"
            class="px-2 py-0.5 text-xs font-medium rounded-full text-brand-primary bg-brand-primary/10 hover:bg-brand-primary/20 cursor-pointer transition-colors"
            @click="handleOpenConvertedSale"
          >
            Venda #{{ String(orcamento.venda_id).padStart(6, '0') }}
          </button>
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
            @click="closeOrcamentoModal()"
          >
            <X :size="20" />
          </button>
        </div>
      </div>
    </template>

    <main class="w-full min-h-[80vh] flex flex-wrap md:flex-nowrap gap-4">
      <section class="w-full md:w-2/3 flex flex-col gap-5">
        <ProductSearch v-if="!orcamento?.convertido" :sale-id="selectedOrcamentoId" is-orcamento :current-items="orcamento?.produtos" />
        <SaleItemsTable :sale="orcamento" :readonly="!!orcamento?.convertido" is-orcamento />
        <SaleSummary
          :subtotal="orcamento?.subtotal"
          :discount="orcamento?.descontos"
          :delivery="orcamento?.entrega"
          :total="orcamento?.total"
        />
      </section>
      <section class="w-full md:w-1/3 flex flex-col min-h-0 max-h-[80vh]">
        <div class="flex-1 overflow-y-scroll flex flex-col gap-4 pr-1">
          <OrcamentoCard :orcamento="orcamento" :readonly="!!orcamento?.convertido" />
        </div>
        <div class="shrink-0 pt-4">
          <div v-if="!orcamento?.convertido" class="flex justify-around gap-5 w-full">
            <BaseButton variant="danger" size="md" class="flex-1" @click="handleDelete">
              <div class="flex flex-col items-center">
                <span>Excluir Orçamento</span>
              </div>
            </BaseButton>
            <BaseButton variant="primary" size="md" class="flex-1" @click="handleConverter">
              <div class="flex flex-col items-center">
                <span>Converter em Venda</span>
                <span class="text-[9px] opacity-70 font-normal">Ctrl+Enter</span>
              </div>
            </BaseButton>
          </div>
          <div v-else class="flex justify-center w-full">
            <BaseButton variant="secondary" size="md" class="flex-1" @click="closeOrcamentoModal()">
              Fechar
            </BaseButton>
          </div>
        </div>
      </section>
    </main>
    <ItemModal :sale-id="selectedOrcamentoId" is-orcamento />
  </BaseModal>
</template>
