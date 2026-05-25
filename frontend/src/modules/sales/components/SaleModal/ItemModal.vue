<script setup lang="ts">
import { X, Info, Tag } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import UnitValueInput from './UnitValueInput.vue';

import { useItemModal } from '../../composables/flows/useItemModal';
import { useItemSaleForm } from '../../composables/form/useItemSaleForm';

import { formatCurrency } from '@/shared/utils/finance';
import { computed } from 'vue';

const props = defineProps<{
  saleId: number | null;
}>();

const { closeItemModal, itemModalIsOpen, isCreateMode, selectedItem } = useItemModal();

const onSucess = () => closeItemModal();

const {
  descricao,
  valorUnitario,
  quantidade,
  desconto,
  subtotal,
  total,
  errors,
  isSubmitting,
  submit,
  resetForm,
  increaseQuantity,
  decreaseQuantity,
} = useItemSaleForm(props.saleId, selectedItem, onSucess);

const displaySubtotal = computed(() => {
  return formatCurrency(subtotal.value * 100);
});

const displayDesconto = computed(() => {
  return formatCurrency(desconto.value * 100);
});

const displayTotal = computed(() => {
  return formatCurrency(total.value * 100);
});

function handleCloseModal() {
  resetForm();
  closeItemModal();
}
</script>

<template>
  <BaseModal :is-open="itemModalIsOpen" title="Produto Avulso" size="lg">
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-zinc-800">
            {{ isCreateMode ? 'Adicionar Produto Avulso' : 'Editar Produto' }}
          </h2>
        </div>

        <button
          type="button"
          class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          @click="handleCloseModal"
        >
          <X :size="20" />
        </button>
      </div>
    </template>

    <div class="w-full flex flex-col">
      <div class="p-4 w-full bg-brand-primary/20 rounded-xl">
        <div class="flex items-center justify-center gap-5">
          <Info :size="35" class="text-brand-primary" />
          <div class="flex flex-col gap-1">
            <h1 class="font-bold text-sm text-brand-primary">
              {{
                isCreateMode
                  ? 'Aqui você pode adicionar um produto avulso à venda'
                  : 'Aqui você pode editar as informações do produto selecionado'
              }}
            </h1>
            <p class="font-medium text-xs text-zinc-500">
              {{
                isCreateMode
                  ? 'Esses produtos não estão cadastrados no estoque e são ideais para itens únicos ou personalizados.'
                  : ' Lembre-se de que essas alterações não afetarão outros produtos ou vendas.'
              }}
            </p>
          </div>
        </div>
      </div>

      <form class="mt-10">
        <div class="grid grid-cols-8 gap-5">
          <div class="col-span-8">
            <BaseInput
              v-model="descricao"
              label="Nome do produto"
              :required="isCreateMode ? true : false"
              :disabled="!isCreateMode"
              placeholder="Insira a descrição do produto"
              :error="errors.descricao"
            />
          </div>
          <div class="col-span-5">
            <MoneyInput
              v-model="valorUnitario"
              :disabled="!isCreateMode"
              :required="isCreateMode ? true : false"
              label="Preço unitário"
              :error="errors.valor_unitario"
            />
          </div>
          <div class="col-span-3 h-full flex flex-col gap-1">
            <label class="text-xs font-medium text-zinc-700"
              >Quantidade <span v-if="isCreateMode" class="text-red-500">*</span>
            </label>
            <UnitValueInput
              v-model="quantidade"
              class="rounded-md"
              @decrease="decreaseQuantity"
              @increase="increaseQuantity"
            />
          </div>
          <div class="col-span-5">
            <MoneyInput
              v-model.number="desconto"
              type="number"
              label="Desconto"
              :max="subtotal"
              :error="errors.desconto"
            />
          </div>
        </div>
      </form>

      <div
        class="p-4 mt-20 w-full bg-brand-primary/10 border border-mid-gray/20 shadow-md rounded-xl"
      >
        <div class="flex items-center">
          <div
            class="w-15 h-15 bg-white rounded-full flex items-center justify-center text-brand-primary"
          >
            <Tag :size="30" />
          </div>

          <div class="w-full flex justify-around">
            <div>
              <h2 class="font-semibold text-[10px] text-mid-gray uppercase">Quantidade</h2>
              <p class="font-bold text-xl sm:text-md text-zinc-700">{{ `${quantidade} un.` }}</p>
            </div>
            <div>
              <h2 class="font-semibold text-[10px] text-mid-gray uppercase">Subtotal</h2>
              <p class="font-bold text-xl sm:text-md text-zinc-700">{{ displaySubtotal }}</p>
            </div>
            <div>
              <h2 class="font-semibold text-[10px] text-mid-gray uppercase">Desconto</h2>
              <p class="font-bold text-xl sm:text-md text-zinc-700">{{ displayDesconto }}</p>
            </div>
            <div>
              <h2 class="font-semibold text-[10px] text-brand-primary/70 uppercase">
                Total do Item
              </h2>
              <p class="font-bold text-xl sm:text-md text-brand-primary">{{ displayTotal }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3">
        <BaseButton variant="secondary" size="md" @click="handleCloseModal">Cancelar</BaseButton>
        <BaseButton variant="primary" size="md" type="submit" :loading="isSubmitting" @click="submit">{{
          isCreateMode ? 'Adicionar' : 'Salvar Alterações'
        }}</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
