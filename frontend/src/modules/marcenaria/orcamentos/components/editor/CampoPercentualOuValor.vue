<script setup lang="ts">
/**
 * @component CampoPercentualOuValor
 * @description Desconto ou sinal em DOIS campos lado a lado, % e R$ (Spec 06B
 * D18; SPEC-00 C7, C9, C8).
 *
 * - O campo que o usuário digita define o MODO (`PERCENTUAL` ou `VALOR`) e é o
 *   que vai para a API.
 * - O outro mostra o EQUIVALENTE em cinza com "≈". O número vem da resposta
 *   da API (`*_centavos` ou `*_bp_efetivo`): nenhuma conta é feita aqui (C8).
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

// Leitura e escrita dos números da tela ("5,5" ↔ 5.5) ficam em utils/conversoes.
const lerNumero = lerNumeroDigitado;
const paraTexto = numeroParaTexto;

// O texto de cada campo enquanto o usuário digita (não brigamos com a digitação).
const textoPercentual = ref('');
const textoValor = ref('');
const focoEm = ref<'PERCENTUAL' | 'VALOR' | null>(null);

/** Preenche os dois campos a partir do modelo e dos equivalentes da API. */
function sincronizar() {
  if (focoEm.value !== 'PERCENTUAL') {
    textoPercentual.value = ajuste.value.modo === 'PERCENTUAL' ? paraTexto(bpParaPercentual(ajuste.value.valor), 2) : '';
  }
  if (focoEm.value !== 'VALOR') {
    textoValor.value = ajuste.value.modo === 'VALOR' ? paraTexto(centavosParaReais(ajuste.value.valor), 2) : '';
  }
}
watch(() => [ajuste.value.modo, ajuste.value.valor], sincronizar, { immediate: true });

/** O usuário digitou no %: o modo vira PERCENTUAL com o número dele. */
function digitarPercentual(evento: Event) {
  textoPercentual.value = (evento.target as HTMLInputElement).value;
  const numero = lerNumero(textoPercentual.value);
  if (numero == null) return;                       // texto inválido: espera o usuário corrigir
  ajuste.value = { modo: 'PERCENTUAL', valor: percentualParaBp(numero) };
}

/** O usuário digitou no R$: o modo vira VALOR com o número dele. */
function digitarValor(evento: Event) {
  textoValor.value = (evento.target as HTMLInputElement).value;
  const numero = lerNumero(textoValor.value);
  if (numero == null) return;
  ajuste.value = { modo: 'VALOR', valor: reaisParaCentavos(numero) };
}

/** Ao sair do campo, o texto volta ao formato limpo. */
function sair() {
  focoEm.value = null;
  sincronizar();
}

// O equivalente (cinza, "≈") de cada lado — vem da API, só formatado aqui.
const equivalentePercentual = computed(() =>
  ajuste.value.modo === 'VALOR' && props.equivalenteBp != null
    ? `≈ ${paraTexto(bpParaPercentual(props.equivalenteBp), 2)}%`
    : '',
);
const equivalenteValor = computed(() =>
  ajuste.value.modo === 'PERCENTUAL' && props.equivalenteCentavos != null
    ? `≈ ${formatCurrency(props.equivalenteCentavos)}`
    : '',
);

/** Dentro do campo de R$ (que já mostra "R$" à esquerda), só o número: "≈ 486,26". */
const placeholderValor = computed(() =>
  ajuste.value.modo === 'PERCENTUAL' && props.equivalenteCentavos != null
    ? `≈ ${centavosParaReais(props.equivalenteCentavos).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '0,00',
);

const CLASSE_CAMPO =
  'w-full rounded-lg border px-3 py-2 text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:bg-zinc-50 disabled:text-zinc-500';
</script>

<template>
  <div>
    <p class="mb-1 text-xs font-medium text-zinc-600">{{ rotulo }}</p>
    <div class="flex items-center gap-2">
      <!-- % -->
      <div class="relative w-28">
        <input
          :value="textoPercentual"
          type="text"
          inputmode="decimal"
          :placeholder="equivalentePercentual || '0'"
          :aria-label="`${rotulo} em percentual`"
          :disabled="disabled"
          :class="[CLASSE_CAMPO, erro ? 'border-red-400' : 'border-zinc-200', ajuste.modo === 'PERCENTUAL' ? 'text-zinc-800' : 'placeholder:text-zinc-400']"
          :data-testid="`${nome}-percentual`"
          @focus="focoEm = 'PERCENTUAL'"
          @input="digitarPercentual"
          @blur="sair"
        />
        <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-400">%</span>
      </div>
      <!-- R$ -->
      <div class="relative w-36">
        <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-zinc-400">R$</span>
        <input
          :value="textoValor"
          type="text"
          inputmode="decimal"
          :placeholder="placeholderValor"
          :aria-label="`${rotulo} em reais`"
          :disabled="disabled"
          :class="[CLASSE_CAMPO, 'pl-9', erro ? 'border-red-400' : 'border-zinc-200', ajuste.modo === 'VALOR' ? 'text-zinc-800' : 'placeholder:text-zinc-400']"
          :data-testid="`${nome}-valor`"
          @focus="focoEm = 'VALOR'"
          @input="digitarValor"
          @blur="sair"
        />
      </div>
    </div>
    <!-- O equivalente também em texto (o placeholder some quando há foco). -->
    <p class="mt-1 text-[11px] text-zinc-400" :data-testid="`${nome}-equivalente`">
      {{ equivalentePercentual || equivalenteValor }}
    </p>
    <p v-if="erro" class="mt-1 text-[11px] text-red-600" role="alert" :data-testid="`${nome}-erro`">{{ erro }}</p>
  </div>
</template>
