<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { refDebounced } from '@vueuse/core';
import { Wrench, ShoppingBag, Plus, Save, Search, Loader2 } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { formatCurrency } from '@/shared/utils/finance';
import { getServicos } from '@/modules/order-service/servicos/services/servicos.service';
import { getProdutos } from '@/modules/products/inventory/services/product.service';
import { MEDIDA_SERVICO_OPTIONS, MEDIDA_PRODUTO_OPTIONS } from '../../constants/core.constant';

import type { OsItemCreateSchemaDataType } from '../../schemas/relationship/osItem.schema';
import type { OsItemMeasureEnumDataType } from '../../schemas/enums/osEnums.schema';

interface CatalogItem {
  id: number;
  nome: string;
  valor: number;
}

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
  'create-new-service': [];
}>();

// ─── Estado do formulário ──────────────────────────────────────────────────────
const tipo = ref<'SERVICO' | 'PRODUTO'>('SERVICO');
const nome = ref('');
const unidade_medida = ref<OsItemMeasureEnumDataType>('UN');
const quantidade = ref(1);
const valorUnitarioNum = ref(0);

// ─── Catálogo de busca ────────────────────────────────────────────────────────
const catalogSearch = ref('');
const debouncedSearch = refDebounced(catalogSearch, 400);
const catalogItems = ref<CatalogItem[]>([]);
const isLoadingCatalog = ref(false);
const selectedCatalogId = ref<number | null>(null);

// ─── Computeds ────────────────────────────────────────────────────────────────
const isService = computed(() => tipo.value === 'SERVICO');

const medidaOptions = computed(() =>
  isService.value ? MEDIDA_SERVICO_OPTIONS : MEDIDA_PRODUTO_OPTIONS,
);

const valorUnitarioCents = computed(() => Math.round((valorUnitarioNum.value ?? 0) * 100));

const total = computed(() => Math.round(quantidade.value * valorUnitarioCents.value));

const isValid = computed(() => nome.value.trim().length > 0 && quantidade.value > 0);

const showCatalogResults = computed(
  () => catalogItems.value.length > 0 && catalogSearch.value.length > 0,
);

// ─── Busca no catálogo ────────────────────────────────────────────────────────
watch(debouncedSearch, async (term) => {
  if (!term || term.length < 2) {
    catalogItems.value = [];
    return;
  }
  isLoadingCatalog.value = true;
  try {
    if (isService.value) {
      const result = await getServicos({ search: term, active: true, limit: 10 });
      catalogItems.value = result.items.map((s) => ({
        id: s.id,
        nome: s.descricao,
        valor: s.valor,
      }));
    } else {
      const result = await getProdutos(term);
      catalogItems.value = result.map((p) => ({
        id: p.id,
        nome: p.nome,
        valor: p.estoque?.valor_varejo ?? 0,
      }));
    }
  } catch {
    catalogItems.value = [];
  } finally {
    isLoadingCatalog.value = false;
  }
});

// Limpa catálogo ao trocar tipo
watch(tipo, () => {
  catalogSearch.value = '';
  catalogItems.value = [];
  selectedCatalogId.value = null;
  unidade_medida.value = 'UN';
});

// ─── Ações ────────────────────────────────────────────────────────────────────
function selectCatalogItem(catalogItem: CatalogItem) {
  selectedCatalogId.value = catalogItem.id;
  nome.value = catalogItem.nome;
  valorUnitarioNum.value = catalogItem.valor / 100;
  catalogSearch.value = catalogItem.nome;
  catalogItems.value = [];
}

function reset() {
  tipo.value = 'SERVICO';
  nome.value = '';
  unidade_medida.value = 'UN';
  quantidade.value = 1;
  valorUnitarioNum.value = 0;
  catalogSearch.value = '';
  catalogItems.value = [];
  selectedCatalogId.value = null;
}

function populate(item: OsItemCreateSchemaDataType) {
  tipo.value = item.tipo;
  nome.value = item.nome;
  unidade_medida.value = item.unidade_medida;
  quantidade.value = item.quantidade;
  valorUnitarioNum.value = item.valor_unitario / 100;
  selectedCatalogId.value = item.item_id ?? null;
  catalogSearch.value = '';
  catalogItems.value = [];
}

watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      if (props.item) {
        populate(props.item);
      } else {
        reset();
      }
    }
  },
);

function handleSave(): void {
  if (!isValid.value) return;

  emit('save', {
    tipo: tipo.value,
    nome: nome.value.trim(),
    unidade_medida: unidade_medida.value,
    quantidade: quantidade.value,
    valor_unitario: valorUnitarioCents.value,
    item_id: selectedCatalogId.value ?? undefined,
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
              :placeholder="isService ? 'Pesquisar serviços cadastrados...' : 'Pesquisar produtos cadastrados...'"
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
            :label="isService ? 'Nome do Serviço' : 'Nome do Produto'"
            :placeholder="isService ? 'Ex: Troca de tela, Formatação...' : 'Ex: Tela LCD, Bateria...'"
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
              :label="isService ? 'Qtd. / Horas' : 'Quantidade'"
              type="number"
              :min="0"
            />
          </div>

          <BaseMoneyInput
            v-model="valorUnitarioNum"
            :label="isService ? 'Valor / Hora' : 'Valor Unitário'"
          />

          <div class="bg-slate-50 rounded-xl p-4 border border-slate-200 flex items-center justify-between">
            <span class="text-sm font-bold text-slate-500 uppercase">Total do Item</span>
            <span class="text-xl font-black text-slate-800">{{ formatCurrency(total) }}</span>
          </div>
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