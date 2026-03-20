<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Wrench, ShoppingBag, Save } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';
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
  save: [item: OsItemCreateSchemaDataType];
}>();

const tipo = ref<OsItemTypeEnumDataType>('SERVICO');
const nome = ref('');
const unidade_medida = ref<OsItemMeasureEnumDataType>('UN');
const quantidade = ref(1);
const valorUnitarioNum = ref(0);

const total = computed(() => Math.round(quantidade.value * valorUnitarioNum.value * 100));
const isValid = computed(() => nome.value.trim().length > 0 && quantidade.value > 0);

const tipoOptions = [
  { value: 'SERVICO', label: 'Serviço / Mão de Obra' },
  { value: 'PRODUTO', label: 'Produto / Peça' },
];

const medidaOptions = [
  { value: 'UN', label: 'Unidade (UN)' },
  { value: 'H', label: 'Hora (H)' },
  { value: 'KG', label: 'Quilograma (KG)' },
  { value: 'G', label: 'Grama (G)' },
  { value: 'L', label: 'Litro (L)' },
  { value: 'ML', label: 'Mililitro (ML)' },
  { value: 'M', label: 'Metro (M)' },
  { value: 'CM', label: 'Centímetro (CM)' },
  { value: 'M2', label: 'Metro² (M2)' },
  { value: 'M3', label: 'Metro³ (M3)' },
  { value: 'D', label: 'Dia (D)' },
  { value: 'MES', label: 'Mês (MES)' },
  { value: 'OUTROS', label: 'Outros' },
];

function reset() {
  tipo.value = 'SERVICO';
  nome.value = '';
  unidade_medida.value = 'UN';
  quantidade.value = 1;
  valorUnitarioNum.value = 0;
}

function populate(item: OsItemCreateSchemaDataType) {
  tipo.value = item.tipo;
  nome.value = item.nome;
  unidade_medida.value = item.unidade_medida;
  quantidade.value = item.quantidade;
  valorUnitarioNum.value = item.valor_unitario / 100;
}

watch(() => props.isOpen, (open) => {
  if (open) {
    if (props.item) populate(props.item);
    else reset();
  }
});

function handleSave() {
  if (!isValid.value) return;
  emit('save', {
    tipo: tipo.value,
    nome: nome.value.trim(),
    unidade_medida: unidade_medida.value,
    quantidade: quantidade.value,
    valor_unitario: Math.round(valorUnitarioNum.value * 100),
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
          @click="tipo = 'SERVICO'"
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
          @click="tipo = 'PRODUTO'"
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
