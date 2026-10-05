<script setup lang="ts">
/**
 * @fileoverview Seção "Insumo da fábrica" do produto (marcenaria-fábrica, F1).
 *
 * Diz como o orçamento consome o produto: a chapa em m², a fita em metro, a
 * ferragem em unidade — e quanto UMA unidade do estoque rende. É com isso que
 * a aprovação do orçamento converte "12 m² de MDF" em "3 chapas" (plano, §5).
 *
 * Mesmo desenho das Embalagens e dos Fornecedores: fora do formulário do
 * produto, rota própria, "Salvar" próprio, só com o produto já salvo. Quem
 * renderiza (ProductModal) já conferiu o segmento.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { Hammer, Save } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

import { fabricaKeys } from '../constants/queryKeys';
import { getInsumo, salvarInsumo } from '../services/fabrica.service';
import type { InsumoEscrita, InsumoRead, UnidadeConsumo } from '../types/fabrica.types';
import { areaDaChapa, comprimentoEmMm, descreverRendimento } from '../utils/insumo';

const props = defineProps<{
  produto: ProdutoRead | null;
  disabled?: boolean;
}>();

const toast = useToast();
const queryClient = useQueryClient();

const produtoId = computed(() => props.produto?.id ?? 0);
const unidadeEstoque = computed(() => props.produto?.unidade_medida || 'UN');

const OPCOES: { valor: UnidadeConsumo | null; rotulo: string }[] = [
  { valor: null, rotulo: 'Não é insumo da fábrica' },
  { valor: 'M2', rotulo: 'Chapa — consumo em m²' },
  { valor: 'M', rotulo: 'Fita, perfil — consumo em metro' },
  { valor: 'UN', rotulo: 'Ferragem, peça — consumo em unidade' },
];

// --- Estado do formulário ---------------------------------------------------

const unidade = ref<UnidadeConsumo | null>(null);
const larguraMm = ref<number | null>(null);
const alturaMm = ref<number | null>(null);
const metros = ref<number | null>(null);
const unidadesPor = ref<number | null>(1);
const sofrePerda = ref(false);
/** O que está gravado: a chapa salva só mostra a área (as medidas não voltam). */
const salvo = ref<InsumoRead | null>(null);
const assinaturaSalva = ref('');

const { data, isLoading } = useQuery({
  queryKey: computed(() => fabricaKeys.insumo(produtoId.value)),
  queryFn: () => getInsumo(produtoId.value),
  enabled: computed(() => produtoId.value > 0),
});

function carregar(insumo: InsumoRead | undefined) {
  if (!insumo) return;
  salvo.value = insumo;
  unidade.value = insumo.unidade_consumo;
  larguraMm.value = null;
  alturaMm.value = null;
  metros.value = insumo.unidade_consumo === 'M' && insumo.consumo_por_unidade ? insumo.consumo_por_unidade / 1000 : null;
  unidadesPor.value = insumo.unidade_consumo === 'UN' ? insumo.consumo_por_unidade : 1;
  sofrePerda.value = insumo.sofre_perda;
  assinaturaSalva.value = JSON.stringify(payload());
}

watch(data, carregar, { immediate: true });

/** Trocar o tipo sugere a perda: chapa e fita perdem no corte, ferragem não. */
function aoTrocarUnidade() {
  sofrePerda.value = unidade.value === 'M2' || unidade.value === 'M';
}

// --- Rendimento ---------------------------------------------------------------

const areaSalva = computed(() =>
  salvo.value?.unidade_consumo === 'M2' ? salvo.value.consumo_por_unidade : null,
);

const rendimento = computed<number | null>(() => {
  if (unidade.value === 'M2') return areaDaChapa(larguraMm.value, alturaMm.value) ?? areaSalva.value;
  if (unidade.value === 'M') return comprimentoEmMm(metros.value);
  if (unidade.value === 'UN') {
    const n = Number(unidadesPor.value);
    return Number.isInteger(n) && n >= 1 ? n : null;
  }
  return null;
});

function payload(): InsumoEscrita {
  return {
    unidade_consumo: unidade.value,
    consumo_por_unidade: unidade.value ? rendimento.value : null,
    sofre_perda: unidade.value ? sofrePerda.value : false,
  };
}

const alterado = computed(() => JSON.stringify(payload()) !== assinaturaSalva.value);

const problema = computed<string | null>(() => {
  if (!unidade.value || rendimento.value) return null;
  if (unidade.value === 'M2') return 'Informe a largura e a altura da chapa, em milímetros.';
  if (unidade.value === 'M') return 'Informe o comprimento do rolo, em metros.';
  return `Informe quantas unidades vêm em cada ${unidadeEstoque.value} (1 se é avulso).`;
});

// --- Salvar ---------------------------------------------------------------------

const mutation = useMutation<InsumoRead, AxiosError<ApiError>, InsumoEscrita>({
  mutationFn: (insumo) => salvarInsumo(produtoId.value, insumo),
  onSuccess: (gravado) => {
    queryClient.setQueryData(fabricaKeys.insumo(produtoId.value), gravado);
    carregar(gravado);
    toast.success(gravado.unidade_consumo ? 'Insumo salvo' : 'O produto deixou de ser insumo');
  },
  onError: (erro) => {
    toast.error('Não foi possível salvar o insumo', getErrorMessage(erro, 'Confira os dados e tente de novo.') as string);
  },
});

function salvar() {
  if (!props.produto || problema.value) return;
  mutation.mutate(payload());
}
</script>

<template>
  <div class="space-y-4">
    <p class="text-xs text-zinc-500">
      Como o orçamento por móvel usa este produto. O estoque continua contado em
      <strong>{{ unidadeEstoque }}</strong>; aqui você diz quanto cada {{ unidadeEstoque }} rende, e o
      sistema converte o consumo do projeto em {{ unidadeEstoque }} inteiras, arredondando para cima.
    </p>

    <div
      v-if="!produto"
      class="flex items-start gap-2 p-3 rounded-xl bg-zinc-50 border border-zinc-200 text-xs text-zinc-600"
    >
      <Hammer :size="15" class="shrink-0 mt-0.5" />
      Salve o produto primeiro; depois, ao editá-lo, dá para marcá-lo como insumo aqui.
    </div>

    <p v-else-if="isLoading" class="text-sm text-zinc-400 text-center py-4">Carregando…</p>

    <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-12 gap-3">
        <label class="campo md:col-span-6">
          <span>Tipo de insumo</span>
          <select v-model="unidade" :disabled="disabled" @change="aoTrocarUnidade">
            <option v-for="o in OPCOES" :key="String(o.valor)" :value="o.valor">{{ o.rotulo }}</option>
          </select>
        </label>

        <template v-if="unidade === 'M2'">
          <label class="campo md:col-span-3">
            <span>Largura da chapa (mm)</span>
            <input v-model.number="larguraMm" :disabled="disabled" type="number" min="1" step="1" placeholder="2750" />
          </label>
          <label class="campo md:col-span-3">
            <span>Altura da chapa (mm)</span>
            <input v-model.number="alturaMm" :disabled="disabled" type="number" min="1" step="1" placeholder="1850" />
          </label>
        </template>

        <label v-else-if="unidade === 'M'" class="campo md:col-span-3">
          <span>Metros por {{ unidadeEstoque }}</span>
          <input v-model.number="metros" :disabled="disabled" type="number" min="0.001" step="0.001" placeholder="50" />
        </label>

        <label v-else-if="unidade === 'UN'" class="campo md:col-span-3">
          <span>Unidades por {{ unidadeEstoque }}</span>
          <input v-model.number="unidadesPor" :disabled="disabled" type="number" min="1" step="1" />
        </label>
      </div>

      <div v-if="unidade" class="flex flex-wrap items-center justify-between gap-3">
        <label class="flex items-center gap-2 text-sm text-zinc-700 cursor-pointer">
          <input v-model="sofrePerda" :disabled="disabled" type="checkbox" class="h-4 w-4 accent-brand-primary" />
          Sofre perda no corte <span class="text-xs text-zinc-500">(a perda % do orçamento entra na quantidade)</span>
        </label>
        <p class="text-xs text-zinc-600">
          Cada {{ unidadeEstoque }} rende <strong>{{ descreverRendimento(unidade, rendimento) }}</strong>
          <template v-if="unidade === 'M2' && areaSalva && !areaDaChapa(larguraMm, alturaMm)">
            (gravado; informe as medidas para trocar)
          </template>
        </p>
      </div>

      <p v-if="problema && !disabled" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
        {{ problema }}
      </p>

      <div v-if="!disabled" class="flex justify-end">
        <BaseButton
          type="button"
          class="flex items-center gap-2"
          :disabled="!alterado || !!problema"
          :is-loading="mutation.isPending.value"
          @click="salvar"
        >
          <Save :size="16" />
          Salvar insumo
        </BaseButton>
      </div>
    </template>
  </div>
</template>

<style scoped>
.campo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}
.campo > span {
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
}
.campo input,
.campo select {
  width: 100%;
  min-width: 0;
  min-height: 2.5rem;
  padding: 0.5rem 0.625rem;
  font-size: 0.875rem;
  border: 1px solid #e4e4e7;
  border-radius: 0.5rem;
  background: #fff;
  outline: none;
}
.campo input:focus,
.campo select:focus {
  border-color: var(--color-brand-primary);
}
.campo input:disabled,
.campo select:disabled {
  background: #f4f4f5;
  color: #71717a;
}
</style>
