<script setup lang="ts">
/**
 * @fileoverview Um móvel do orçamento: nome, medidas, preço e a lista de
 * material. O custo é PRÉVIA (utils/calculo.ts); salvar recalcula no servidor.
 */
import { computed } from 'vue';
import { Trash2, X } from 'lucide-vue-next';

import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { InsumoBusca } from '../types/fabrica.types';
import { ROTULO_CONSUMO } from '../utils/calculo';
import { custoMaterial, custoMovel, materialDe, precoSugerido, type MovelEdit } from '../utils/editor';
import InsumoPicker from './InsumoPicker.vue';

const movel = defineModel<MovelEdit>({ required: true });

const props = defineProps<{
  perdaPercentual: number | null;
  margemPadrao: number;
  editavel: boolean;
  /** Linha "Fábrica" de Cargos, Visualizar: sem ela, nada de custo nem preço sugerido. */
  mostrarCusto: boolean;
}>();

const emit = defineEmits<{ remover: [] }>();

const custo = computed(() => custoMovel(movel.value, props.perdaPercentual));
const sugerido = computed(() => precoSugerido(custo.value, props.margemPadrao));

function adicionar(insumo: InsumoBusca) {
  movel.value.materiais.push(materialDe(insumo));
}

function removerMaterial(chave: number) {
  movel.value.materiais = movel.value.materiais.filter((m) => m.chave !== chave);
}

function usarSugerido() {
  if (sugerido.value != null) movel.value.precoReais = sugerido.value;
}
</script>

<template>
  <div class="rounded-xl border border-zinc-200 bg-white p-4 space-y-3">
    <div class="grid grid-cols-2 md:grid-cols-12 gap-3 items-end">
      <label class="campo col-span-2 md:col-span-5">
        <span>Móvel</span>
        <input v-model="movel.nome" :disabled="!editavel" maxlength="120" placeholder="Ex.: Armário aéreo" />
      </label>
      <label class="campo md:col-span-2">
        <span>Largura (mm)</span>
        <input v-model.number="movel.largura_mm" :disabled="!editavel" type="number" min="1" step="1" />
      </label>
      <label class="campo md:col-span-2">
        <span>Altura (mm)</span>
        <input v-model.number="movel.altura_mm" :disabled="!editavel" type="number" min="1" step="1" />
      </label>
      <label class="campo md:col-span-2">
        <span>Profund. (mm)</span>
        <input v-model.number="movel.profundidade_mm" :disabled="!editavel" type="number" min="1" step="1" />
      </label>
      <div class="md:col-span-1 flex justify-end">
        <button
          v-if="editavel"
          type="button"
          class="p-2 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
          title="Tirar este móvel"
          @click="emit('remover')"
        >
          <Trash2 :size="16" />
        </button>
      </div>
    </div>

    <!-- Material -->
    <div class="rounded-lg bg-zinc-50 border border-zinc-100 p-3 space-y-2">
      <p class="text-[11px] font-bold uppercase tracking-wider text-zinc-500">Material</p>
      <div
        v-for="m in movel.materiais"
        :key="m.chave"
        class="grid grid-cols-12 gap-2 items-center text-sm"
      >
        <span class="col-span-6 truncate" :title="m.descricao">{{ m.descricao }}</span>
        <div class="col-span-3 flex items-center gap-1">
          <input
            v-model.number="m.quantidade"
            :disabled="!editavel"
            type="number"
            min="0"
            :step="m.unidade_consumo === 'UN' ? 1 : 0.01"
            class="w-full min-h-8 px-2 text-sm border border-zinc-200 rounded-md bg-white outline-none focus:border-brand-primary disabled:bg-zinc-100"
          />
          <span class="text-xs text-zinc-500 w-6">{{ ROTULO_CONSUMO[m.unidade_consumo] }}</span>
        </div>
        <span class="col-span-2 text-right tabular-nums text-zinc-600">
          <template v-if="mostrarCusto">{{ formatCurrency(custoMaterial(m, perdaPercentual)) }}</template>
        </span>
        <div class="col-span-1 flex justify-end">
          <button
            v-if="editavel"
            type="button"
            class="p-1 rounded text-zinc-400 hover:text-red-600 cursor-pointer"
            title="Tirar este material"
            @click="removerMaterial(m.chave)"
          >
            <X :size="14" />
          </button>
        </div>
      </div>
      <p v-if="!movel.materiais.length" class="text-xs text-zinc-400">
        Sem material — tudo bem para móvel terceirizado ou serviço.
      </p>
      <InsumoPicker v-if="editavel" @escolher="adicionar" />
    </div>

    <!-- Terceiro e preço -->
    <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
      <div class="md:col-span-4 space-y-2">
        <label class="flex items-center gap-2 text-sm text-zinc-700 cursor-pointer">
          <input v-model="movel.terceirizado" :disabled="!editavel" type="checkbox" class="h-4 w-4 accent-brand-primary" />
          Terceirizado (central de corte, outra fábrica)
        </label>
        <BaseMoneyInput
          v-if="movel.terceirizado && mostrarCusto"
          v-model="movel.custoTerceiroReais"
          label="Custo do terceiro"
          :disabled="!editavel"
        />
      </div>
      <div class="md:col-span-4 text-sm text-zinc-600 pb-2.5">
        <template v-if="mostrarCusto">
        Custo: <strong class="tabular-nums">{{ formatCurrency(custo) }}</strong>
        <button
          v-if="editavel && sugerido != null"
          type="button"
          class="block text-xs text-brand-primary hover:underline cursor-pointer"
          :title="`Custo + ${margemPadrao}% (margem padrão de Produtos)`"
          @click="usarSugerido"
        >
          Usar preço sugerido: {{ formatCurrency(Math.round(sugerido * 100)) }}
        </button>
        </template>
      </div>
      <div class="md:col-span-4">
        <BaseMoneyInput v-model="movel.precoReais" label="Preço de venda" :disabled="!editavel" />
      </div>
    </div>
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
.campo input {
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
.campo input:focus {
  border-color: var(--color-brand-primary);
}
.campo input:disabled {
  background: #f4f4f5;
  color: #71717a;
}
</style>
