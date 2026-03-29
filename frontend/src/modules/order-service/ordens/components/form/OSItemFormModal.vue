<script setup lang="ts">
import { watch } from 'vue';
import { Wrench, ShoppingBag, Plus, Save } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { useProductsQuery } from '@/modules/products/composables/useProductsQuery';
import { getServicos } from '@/modules/order-service/servicos/services/servicos.service';
import { MEDIDA_SERVICO_OPTIONS, MEDIDA_PRODUTO_OPTIONS } from '../../constants/core.constant';
import type { OsItemCreateSchemaDataType } from '../../schemas/relationship/osItem.schema';
import type { OsItemTypeEnumDataType, OsItemMeasureEnumDataType } from '../../schemas/enums/osEnums.schema';

interface Props {
  isOpen: boolean;
  item?: OsItemCreateSchemaDataType | null;
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  item: null,
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

function handleSave(): void {
  if (!isValid.value) return;

  const options = isService.value ? props.servicosOptions : props.produtosOptions;
  const selectedOption = options.find((o) => String(o.value) === String(servicoId.value));
  const nome = selectedOption?.label ?? descricao.value ?? '';

  emit('save', {
    servico_id: servicoId.value ? Number(servicoId.value) : undefined,
    descricao: descricao.value,
    quantidade: quantidade.value,
    valor_unitario: valorUnitarioCents.value,
  });
  emit('close');
}

function handleClose(): void {
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
    <form @submit.prevent="handleSave" class="space-y-5">
      <!-- Toggle Tipo -->
      <div class="flex p-1 bg-slate-100 rounded-lg">
        <button
          type="button"
          @click="type = 'servicos'"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 text-sm font-bold rounded-md transition-all',
            tipo === 'SERVICO' ? 'bg-white text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-700',
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
            tipo === 'PRODUTO' ? 'bg-white text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-700',
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

        <div class="relative">
          <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            v-model="catalogSearch"
            type="text"
            :placeholder="tipo === 'SERVICO' ? 'Pesquisar serviços cadastrados...' : 'Pesquisar produtos cadastrados...'"
            class="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary placeholder:text-slate-400"
          />
          <Loader2
            v-if="isLoadingCatalog && catalogSearch.length > 0"
            :size="16"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 animate-spin"
          />
        </div>

        <div
          v-if="showCatalogResults"
          class="max-h-36 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 bg-white shadow-sm"
        >
          <button
            v-for="catalogItem in catalogItems"
            :key="catalogItem.id"
            type="button"
            @click="selectCatalogItem(catalogItem)"
            :class="[
              'w-full flex items-center justify-between px-3 py-2.5 text-left transition-colors',
              selectedCatalogId === catalogItem.id
                ? 'bg-brand-primary-light text-brand-primary'
                : 'hover:bg-slate-50',
            ]"
          >
            <span class="text-sm font-medium text-slate-700 truncate">{{ catalogItem.nome }}</span>
            <span class="text-sm font-bold text-slate-600 shrink-0 ml-3">
              {{ formatCurrency(catalogItem.valor) }}
            </span>
          </button>
        </div>

        <p
          v-else-if="catalogSearch.length > 0 && !isLoadingCatalog && catalogItems.length === 0"
          class="text-xs text-slate-400 italic py-1"
        >
          Nenhum resultado encontrado. Preencha manualmente abaixo.
        </p>
      </div>

      <!-- Separador -->
      <div class="relative flex items-center gap-3">
        <div class="flex-1 border-t border-slate-200"></div>
        <span class="text-xs text-slate-400 font-medium">ou preencha manualmente</span>
        <div class="flex-1 border-t border-slate-200"></div>
      </div>

      <!-- Campos do formulário -->
      <div class="space-y-4">
        <BaseInput
          v-model="nome"
          :label="tipo === 'SERVICO' ? 'Nome do Serviço' : 'Nome do Produto'"
          :placeholder="tipo === 'SERVICO' ? 'Ex: Troca de tela, Formatação...' : 'Ex: Tela LCD, Bateria...'"
          required
        />

        <div class="grid grid-cols-2 gap-4">
          <BaseSelect
            v-model="unidade_medida"
            label="Unidade de Medida"
            :options="medidaOptions"
          />

          <BaseInput
            v-model.number="quantidade"
            :label="tipo === 'SERVICO' ? 'Qtd. / Horas' : 'Quantidade'"
            type="number"
            :min="0"
          />
        </div>

        <BaseMoneyInput
          v-model="valorUnitarioNum"
          :label="tipo === 'SERVICO' ? 'Valor / Hora' : 'Valor Unitário'"
        />

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
