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
 *
 * Dois recursos OPCIONAIS (Spec 12B, etapas de um móvel da OS); sem eles, o
 * editor é exatamente o de Configurações › Marcenaria:
 * - `ids` (v-model:ids): a identidade de cada item, que ANDA com ele ao subir,
 *   descer e remover. Item novo entra com `null`. Serve para o pai saber qual
 *   etapa foi renomeada ou movida.
 * - `travados`: itens que não podem ser renomeados nem removidos (etapa já
 *   concluída). Subir e descer continuam valendo. O motivo vai no `title`.
 */
import { computed, nextTick, ref } from 'vue';
import { ChevronDown, ChevronUp, Plus, X } from 'lucide-vue-next';

import { errosDosItens } from './errosDosItens';

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
  /** Opcional: a identidade de cada item, na mesma ordem (v-model:ids). */
  ids?: (number | null)[];
  /** Opcional: por item, se está travado (sem renomear nem remover). */
  travados?: boolean[];
  /** Por que o item está travado (vai no `title` do campo e do botão de remover). */
  motivoTravado?: string;
}

const props = withDefaults(defineProps<Props>(), { disabled: false, ids: undefined, travados: undefined, motivoTravado: '' });

const emit = defineEmits<{
  'update:modelValue': [value: string[]];
  'update:ids': [value: (number | null)[]];
}>();

/** O item da posição está travado? */
const travado = (indice: number) => props.travados?.[indice] === true;

/** Os campos de texto, para mandar o foco ao item novo. */
const campos = ref<HTMLInputElement[]>([]);

/** Erro de cada item ('' = certo), com a mesma regra do backend. */
const erros = computed(() => errosDosItens(props.modelValue, props.maxCaracteres));

/**
 * Sempre devolve uma lista NOVA: o pai recebe a mudança pelo v-model. Com
 * `ids`, a lista de identidades vai junto, na mesma ordem.
 */
function emitir(lista: string[], ids?: (number | null)[]) {
  emit('update:modelValue', lista);
  if (props.ids && ids) emit('update:ids', ids);
}

function editar(indice: number, valor: string) {
  if (travado(indice)) return;               // travado: o nome não muda
  const lista = [...props.modelValue];
  lista[indice] = valor;                     // troca só o item editado
  emitir(lista);
}

async function adicionar() {
  if (props.disabled || props.modelValue.length >= props.maxItens) return;
  emitir([...props.modelValue, ''], [...(props.ids ?? []), null]);   // item vazio no fim (novo: sem id)
  await nextTick();                          // espera o campo novo aparecer
  campos.value[props.modelValue.length - 1]?.focus();
}

function remover(indice: number) {
  if (props.disabled || props.modelValue.length <= 1 || travado(indice)) return;   // o último não sai (D14)
  emitir(props.modelValue.filter((_, i) => i !== indice), props.ids?.filter((_, i) => i !== indice));
}

/** Troca o item de lugar com o vizinho (direcao -1 = sobe, +1 = desce). */
function mover(indice: number, direcao: -1 | 1) {
  const destino = indice + direcao;
  if (props.disabled || destino < 0 || destino >= props.modelValue.length) return;
  const lista = [...props.modelValue];
  [lista[indice], lista[destino]] = [lista[destino], lista[indice]];
  // A identidade troca de lugar junto com o texto.
  const ids = props.ids ? [...props.ids] : undefined;
  if (ids) [ids[indice], ids[destino]] = [ids[destino], ids[indice]];
  emitir(lista, ids);
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
          :readonly="travado(indice)"
          :title="travado(indice) ? motivoTravado : undefined"
          :aria-label="`${rotuloItem} ${indice + 1}`"
          :aria-invalid="erros[indice] ? 'true' : 'false'"
          class="flex-1 border rounded-lg px-3 py-1.5 text-sm text-zinc-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary disabled:bg-zinc-50 disabled:text-zinc-500"
          :class="[erros[indice] ? 'border-red-300' : 'border-zinc-200', travado(indice) ? 'bg-zinc-50 text-zinc-500' : '']"
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
          :disabled="disabled || modelValue.length <= 1 || travado(indice)"
          :title="travado(indice) ? motivoTravado : undefined"
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
