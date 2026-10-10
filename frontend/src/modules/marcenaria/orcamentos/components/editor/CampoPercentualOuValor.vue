<script setup lang="ts">
/**
 * @component CampoPercentualOuValor
 * @description Desconto ou sinal: um seletor "% | R$" e UM campo (Spec 06B
 * D18, revisto no redesign 10/2026; SPEC-00 C7, C9, C8).
 *
 * - O seletor define o MODO (`PERCENTUAL` ou `VALOR`); o campo mostra o número
 *   nesse modo, e é o que vai para a API.
 * - Trocar o modo NÃO muda o desconto: o campo passa a mostrar o equivalente
 *   que a API já calculou (`*_centavos` ou `*_bp_efetivo`). Nenhuma conta é
 *   feita aqui (C8).
 * - Embaixo, o equivalente no outro modo, com "≈".
 */
import { computed, ref, watch } from 'vue';

import { formatCurrency } from '@/shared/utils/finance';

import type { AjusteOrcamento } from '../../schemas/orcamentoDetalhe.schema';
import {
  bpParaPercentual,
  centavosParaReais,
  lerNumeroDigitado,
  numeroParaTexto,
  percentualParaBp,
  reaisParaCentavos,
} from '../../utils/conversoes';

const props = defineProps<{
  rotulo: string;
  /** Equivalente em R$ calculado pela API (ex.: `calculo.desconto_centavos`). */
  equivalenteCentavos: number | null;
  /** Equivalente em % calculado pela API (ex.: `calculo.desconto_bp_efetivo`). */
  equivalenteBp: number | null;
  erro?: string;
  disabled?: boolean;
  /** Prefixo dos data-testid (ex.: "desconto"). */
  nome: string;
}>();

const ajuste = defineModel<AjusteOrcamento>({ required: true });

const percentual = computed(() => ajuste.value.modo === 'PERCENTUAL');

// O texto do campo enquanto o usuário digita (não brigamos com a digitação).
const texto = ref('');
const comFoco = ref(false);

/** O campo a partir do modelo: "5,5" no %, "486,26" no R$. */
function sincronizar() {
  if (comFoco.value) return;
  texto.value = percentual.value
    ? numeroParaTexto(bpParaPercentual(ajuste.value.valor), 2)
    : numeroParaTexto(centavosParaReais(ajuste.value.valor), 2);
}
watch(() => [ajuste.value.modo, ajuste.value.valor], sincronizar, { immediate: true });

function digitar(evento: Event) {
  texto.value = (evento.target as HTMLInputElement).value;
  const numero = lerNumeroDigitado(texto.value);
  if (numero == null) return;                       // texto inválido: espera o usuário corrigir
  ajuste.value = percentual.value
    ? { modo: 'PERCENTUAL', valor: percentualParaBp(numero) }
    : { modo: 'VALOR', valor: reaisParaCentavos(numero) };
}

/** Ao sair do campo, o texto volta ao formato limpo. */
function sair() {
  comFoco.value = false;
  sincronizar();
}

/** Trocar % ↔ R$ mantém o mesmo desconto: usa o equivalente que a API calculou. */
function trocarModo(modo: AjusteOrcamento['modo']) {
  if (props.disabled || modo === ajuste.value.modo) return;
  ajuste.value = modo === 'VALOR'
    ? { modo, valor: props.equivalenteCentavos ?? 0 }
    : { modo, valor: props.equivalenteBp ?? 0 };
}

// O equivalente no outro modo (cinza, "≈") — vem da API, só formatado aqui.
const equivalente = computed(() => {
  if (!percentual.value && props.equivalenteBp != null) return `≈ ${numeroParaTexto(bpParaPercentual(props.equivalenteBp), 2)}%`;
  if (percentual.value && props.equivalenteCentavos != null) return `≈ ${formatCurrency(props.equivalenteCentavos)}`;
  return '';
});

const CLASSE_MODO = 'min-h-10 px-3 text-xs font-semibold transition-colors disabled:cursor-not-allowed';
</script>

<template>
  <div>
    <p class="mb-1.5 text-xs font-medium text-zinc-600">{{ rotulo }}</p>
    <div class="flex gap-1.5">
      <!-- % | R$ -->
      <div class="flex shrink-0 overflow-hidden rounded-md border border-gray-300" role="radiogroup" :aria-label="`${rotulo} em`">
        <button
          type="button"
          role="radio"
          :aria-checked="percentual"
          :disabled="disabled"
          :class="[CLASSE_MODO, percentual ? 'bg-zinc-900 text-white' : 'bg-white text-zinc-500 hover:bg-zinc-50 cursor-pointer']"
          :data-testid="`${nome}-modo-percentual`"
          @click="trocarModo('PERCENTUAL')"
        >
          %
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="!percentual"
          :disabled="disabled"
          :class="[CLASSE_MODO, !percentual ? 'bg-zinc-900 text-white' : 'bg-white text-zinc-500 hover:bg-zinc-50 cursor-pointer']"
          :data-testid="`${nome}-modo-valor`"
          @click="trocarModo('VALOR')"
        >
          R$
        </button>
      </div>
      <!-- O campo do modo escolhido (o data-testid diz qual: "-percentual" ou "-valor") -->
      <div class="relative min-w-0 flex-1">
        <span v-if="!percentual" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-zinc-500">R$</span>
        <input
          :value="texto"
          type="text"
          inputmode="decimal"
          placeholder="0"
          :aria-label="percentual ? `${rotulo} em percentual` : `${rotulo} em reais`"
          :disabled="disabled"
          :class="[
            'min-h-10 w-full rounded-md border bg-white py-2 text-sm tabular-nums text-gray-700 outline-none placeholder:text-gray-400 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary disabled:bg-gray-100 disabled:cursor-not-allowed',
            percentual ? 'pl-3 pr-8' : 'pl-9 pr-3',
            erro ? 'border-red-400' : 'border-gray-300',
          ]"
          :data-testid="percentual ? `${nome}-percentual` : `${nome}-valor`"
          @focus="comFoco = true"
          @input="digitar"
          @blur="sair"
        />
        <span v-if="percentual" class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-zinc-500">%</span>
      </div>
    </div>
    <p class="mt-1.5 min-h-4 text-xs tabular-nums text-zinc-500" :data-testid="`${nome}-equivalente`">{{ equivalente }}</p>
    <p v-if="erro" class="mt-1 text-xs text-red-600" role="alert" :data-testid="`${nome}-erro`">{{ erro }}</p>
  </div>
</template>
