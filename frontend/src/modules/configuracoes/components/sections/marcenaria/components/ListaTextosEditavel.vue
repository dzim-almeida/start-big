<script setup lang="ts">
/**
 * @component ListaTextosEditavel
 * @description Edita uma lista curta de textos (etapas de produção, checklist
 * de vistoria): adicionar no fim, editar no lugar, subir, descer e remover
 * (Spec 04B, D14). Não sabe o que é etapa ou checklist: só a lista.
 *
 * Regras iguais às do backend (Spec 04A §6.4): nunca fica vazia (o último item
 * não sai), recusa item vazio, longo demais e repetido — o erro aparece ao
 * digitar, ao lado do item, e não só ao salvar.
 */
import { computed, nextTick, ref } from 'vue';
import { ChevronDown, ChevronUp, Plus, X } from 'lucide-vue-next';

import { errosDosItens } from '../marcenariaForm';

interface Props {
  /** A lista atual (v-model). */
  modelValue: string[];
  /** Quantos itens cabem, no máximo. */
  maxItens: number;
  /** Tamanho máximo de cada item. */
  maxCaracteres: number;
  /** Nome de UM item ("etapa", "item do checklist"): vai nos botões e nos aria-label. */
  rotuloItem: string;
  /** Somente leitura (sem permissão de alterar). */
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), { disabled: false });

const emit = defineEmits<{
  'update:modelValue': [value: string[]];
}>();

/** Os campos de texto, para mandar o foco ao item novo. */
const campos = ref<HTMLInputElement[]>([]);

/** Erro de cada item ('' = certo), com a mesma regra do backend. */
const erros = computed(() => errosDosItens(props.modelValue, props.maxCaracteres));

/** Sempre devolve uma lista NOVA: o pai recebe a mudança pelo v-model. */
function emitir(lista: string[]) {
  emit('update:modelValue', lista);
}

function editar(indice: number, valor: string) {
  const lista = [...props.modelValue];
  lista[indice] = valor;                     // troca só o item editado
  emitir(lista);
}

async function adicionar() {
  if (props.disabled || props.modelValue.length >= props.maxItens) return;
  emitir([...props.modelValue, '']);         // item vazio no fim
  await nextTick();                          // espera o campo novo aparecer
  campos.value[props.modelValue.length - 1]?.focus();
}

function remover(indice: number) {
  if (props.disabled || props.modelValue.length <= 1) return;   // o último não sai (D14)
  emitir(props.modelValue.filter((_, i) => i !== indice));
}

/** Troca o item de lugar com o vizinho (direcao -1 = sobe, +1 = desce). */
function mover(indice: number, direcao: -1 | 1) {
  const destino = indice + direcao;
  if (props.disabled || destino < 0 || destino >= props.modelValue.length) return;
  const lista = [...props.modelValue];
  [lista[indice], lista[destino]] = [lista[destino], lista[indice]];
  emitir(lista);
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div v-for="(item, indice) in modelValue" :key="indice" class="flex flex-col gap-0.5">
      <div class="flex items-center gap-2">
        <span class="w-5 text-right text-[11px] text-zinc-400 tabular-nums">{{ indice + 1 }}.</span>
        <input
          :ref="(el) => { if (el) campos[indice] = el as HTMLInputElement }"
          :value="item"
          type="text"
          :maxlength="maxCaracteres"
          :disabled="disabled"
          :aria-label="`${rotuloItem} ${indice + 1}`"
          :aria-invalid="erros[indice] ? 'true' : 'false'"
          class="flex-1 border rounded-lg px-3 py-1.5 text-sm text-zinc-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary disabled:bg-zinc-50 disabled:text-zinc-500"
          :class="erros[indice] ? 'border-red-300' : 'border-zinc-200'"
          @input="editar(indice, ($event.target as HTMLInputElement).value)"
        />
        <button
          type="button"
          class="p-1 rounded text-zinc-400 hover:text-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed"
          :disabled="disabled || indice === 0"
          :aria-label="`Subir ${rotuloItem} ${item}`"
          @click="mover(indice, -1)"
        >
          <ChevronUp :size="16" />
        </button>
        <button
          type="button"
          class="p-1 rounded text-zinc-400 hover:text-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed"
          :disabled="disabled || indice === modelValue.length - 1"
          :aria-label="`Descer ${rotuloItem} ${item}`"
          @click="mover(indice, 1)"
        >
          <ChevronDown :size="16" />
        </button>
        <button
          type="button"
          class="p-1 rounded text-zinc-400 hover:text-red-600 disabled:opacity-30 disabled:cursor-not-allowed"
          :disabled="disabled || modelValue.length <= 1"
          :aria-label="`Remover ${rotuloItem} ${item}`"
          @click="remover(indice)"
        >
          <X :size="16" />
        </button>
      </div>
      <!-- Erro do item, ao lado dele (vazio, longo demais ou repetido). -->
      <p v-if="erros[indice]" class="ml-7 text-[11px] text-red-600" data-testid="erro-item">{{ erros[indice] }}</p>
    </div>

    <button
      v-if="!disabled"
      type="button"
      class="self-start mt-1 inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline disabled:opacity-40 disabled:no-underline disabled:cursor-not-allowed"
      :disabled="modelValue.length >= maxItens"
      @click="adicionar"
    >
      <Plus :size="12" />
      Adicionar {{ rotuloItem }}
    </button>
  </div>
</template>
