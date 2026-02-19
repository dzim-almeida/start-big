<!--
===========================================================================
ARQUIVO: OSItemFormModal.vue
MODULO: Ordem de Servico
DESCRICAO: Modal para adicao/edicao de itens (servicos ou produtos) na OS.
           Permite selecao do catalogo com auto-preenchimento de valores.
===========================================================================

PROPS:
- isOpen: Controla visibilidade do modal
- item: Item existente para edicao (null para novo)
- servicosOptions: Lista de servicos disponiveis
- produtosOptions: Lista de produtos disponiveis
- isLoadingServicos/isLoadingProdutos: Estados de carregamento

EMITS:
- close: Fecha o modal
- save: Salva item { servico_id, descricao, quantidade, valor_unitario }
- create-new-service: Abre modal de criacao rapida de servico

FUNCIONALIDADES:
- Toggle entre Servico e Produto
- Selecao de item do catalogo
- Auto-preenchimento de preco e descricao ao selecionar
- Campos editaveis: quantidade, valor unitario, descricao
- Calculo automatico do total do item
- Validacao de campos obrigatorios

DEPENDENCIAS:
- useOSItemForm: Gerencia estado do formulario
===========================================================================
-->
<script setup lang="ts">
import { watch } from 'vue';
import {
  Wrench,
  ShoppingBag,
  Plus,
  Save,
  Clock,
  DollarSign,
  Type
} from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/commons/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/commons/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { OrdemServicoItemCreate } from '@/modules/ordemServico/types/ordemServico.types';
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

// Composable
const {
  type,
  servicoId,
  descricao,
  quantidade,
  valorUnitario,
  isService,
  valorUnitarioCents,
  total,
  isValid,
  reset,
  populate,
  handleValorInput
} = useOSItemForm(props);

// Init
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
      
      <!-- Type Toggle -->
      <div class="flex p-1 bg-slate-100 rounded-lg">
        <button
          type="button"
          @click="type = 'servicos'"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 text-sm font-bold rounded-md transition-all',
            isService 
              ? 'bg-white text-brand-primary shadow-sm' 
              : 'text-slate-500 hover:text-slate-700'
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
            !isService 
              ? 'bg-white text-brand-primary shadow-sm' 
              : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          <ShoppingBag :size="16" />
          Produto / Peça
        </button>
      </div>

      <!-- Form Fields -->
      <div class="space-y-4">
        
        <!-- Selection Row -->
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

        <!-- Description -->
        <div class="space-y-1.5">
           <BaseInput
              v-model="descricao"
              label="Descrição (Op. na OS)"
              placeholder="Detalhes adicionais do serviço ou peça..."
              :left-icon="Type"
           />
        </div>

        <!-- Values Row -->
        <div class="grid grid-cols-2 gap-4">
          <!-- Quantity / Hours -->
          <div class="space-y-1.5">
             <BaseInput
                v-model.number="quantidade"
                :label="isService ? 'Qtd. / Horas' : 'Quantidade'"
                type="number"
                :left-icon="Clock"
             />
          </div>

          <!-- Unit Value / Hourly Rate -->
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-slate-500 uppercase flex items-center gap-1 mb-1">
              <DollarSign :size="12" />
              {{ isService ? 'Valor / Hora' : 'Valor Unitário' }}
            </label>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-medium">R$</span>
              <input 
                :value="valorUnitario"
                @input="handleValorInput"
                type="text"
                class="w-full pl-9 pr-3 py-2 border rounded-md transition-colors duration-200 outline-none text-sm placeholder:text-gray-400 text-gray-700 border-gray-300 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary bg-white text-right"
              />
            </div>
          </div>
        </div>

        <!-- Total Display -->
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
        <BaseButton
          type="submit"
          variant="primary"
          :disabled="!isValid"
          @click="handleSave"
        >
          <Save :size="16" class="mr-2" />
          {{ item ? 'SALVAR ALTERAÇÕES' : 'ADICIONAR ITEM' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
