<script setup lang="ts">
import { watch } from 'vue';
import { Wrench, ShoppingBag, Plus, Save } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { OrdemServicoItemCreate } from '../../types/ordemServico.types';
import { useOSItemForm, type SelectOption } from '../../composables/useOSItemForm';

interface Props {
  isOpen: boolean;
  item?: OrdemServicoItemCreate | null;
  servicosOptions: SelectOption[];
  produtosOptions: SelectOption[];
  isLoadingServicos?: boolean;
  isLoadingProdutos?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  item: null,
  servicosOptions: () => [],
  produtosOptions: () => [],
  isLoadingServicos: false,
  isLoadingProdutos: false,
});

const emit = defineEmits<{
  close: [];
  save: [item: OrdemServicoItemCreate];
  'create-new-service': [];
}>();

const {
  type,
  servicoId,
  descricao,
  quantidade,
  valorUnitarioNum,
  isService,
  valorUnitarioCents,
  total,
  isValid,
  reset,
  populate,
} = useOSItemForm(props);

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    if (props.item) {
      populate(props.item);
    } else {
      reset();
    }
  }
});

function handleSave() {
  if (!isValid.value) return;
  emit('save', {
    servico_id: servicoId.value ? Number(servicoId.value) : undefined,
    descricao: descricao.value,
    quantidade: quantidade.value,
    valor_unitario: valorUnitarioCents.value,
  });
  emit('close');
}

function handleClose() {
  emit('close');
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="item ? 'Editar Item' : 'Adicionar Item'"
    size="lg"
    @close="handleClose"
  >
    <form @submit.prevent="handleSave" class="space-y-6">
      <div class="flex p-1 bg-slate-100 rounded-lg">
        <button
          type="button"
          @click="type = 'servicos'"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 text-sm font-bold rounded-md transition-all',
            isService ? 'bg-white text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-700',
          ]"
        >
          <Wrench :size="16" />
          Serviço / Mão de Obra
        </button>
        <button
          type="button"
          @click="type = 'produtos'"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 text-sm font-bold rounded-md transition-all',
            !isService ? 'bg-white text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-700',
          ]"
        >
          <ShoppingBag :size="16" />
          Produto / Peça
        </button>
      </div>

      <div class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase flex items-center justify-between">
            {{ isService ? 'Serviço' : 'Produto' }}
            <button
              v-if="isService"
              type="button"
              class="text-[10px] text-brand-primary hover:text-brand-primary/80 flex items-center gap-1 bg-brand-primary-light px-2 py-0.5 rounded-full"
              @click="$emit('create-new-service')"
            >
              <Plus :size="10" /> NOVO SERVIÇO
            </button>
          </label>

          <BaseSelect
            v-if="isService"
            v-model="servicoId"
            :options="servicosOptions"
            placeholder="Selecione um serviço..."
            class="w-full"
            :empty-message="isLoadingServicos ? 'Carregando...' : 'Nenhum serviço encontrado'"
          />
          <BaseSelect
            v-else
            v-model="servicoId"
            :options="produtosOptions"
            placeholder="Selecione um produto..."
            class="w-full"
            :empty-message="isLoadingProdutos ? 'Carregando...' : 'Nenhum produto encontrado'"
          />
        </div>

        <div class="space-y-1.5">
          <BaseInput
            v-model="descricao"
            label="Descrição (Op. na OS)"
            placeholder="Detalhes adicionais do serviço ou peça..."
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <BaseInput
              v-model.number="quantidade"
              :label="isService ? 'Qtd. / Horas' : 'Quantidade'"
              type="number"
            />
          </div>

          <BaseMoneyInput
            v-model="valorUnitarioNum"
            :label="isService ? 'Valor / Hora' : 'Valor Unitário'"
          />
        </div>

        <div class="bg-slate-50 rounded-xl p-4 border border-slate-200 flex items-center justify-between">
          <span class="text-sm font-bold text-slate-500 uppercase">Total do Item</span>
          <span class="text-xl font-black text-slate-800">{{ formatCurrency(total) }}</span>
        </div>
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <BaseButton variant="secondary" @click="handleClose">
          CANCELAR
        </BaseButton>
        <BaseButton type="submit" variant="primary" :disabled="!isValid" @click="handleSave">
          <Save :size="16" class="mr-2" />
          {{ item ? 'SALVAR ALTERAÇÕES' : 'ADICIONAR ITEM' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
