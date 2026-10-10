<script setup lang="ts">
/**
 * @component BlocoInstalacao
 * @description Instalação do orçamento (Spec 06B §6.2, D16; SPEC-00 C3) — a
 * coluna da esquerda da seção "Instalação e medição" (redesign 10/2026).
 *
 * - Quem vê custos: chave "Cobrar instalação" + custo; o PREÇO vem da API.
 *   Chave desligada manda `instalacao_custo_centavos = null` (sem a linha).
 * - Quem não vê custos: só o preço (o custo nem chega na resposta).
 */
import { computed } from 'vue';

import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useEditor } from '../../composables/useEditorContexto';
import { centavosParaReais, formatarBp, reaisParaCentavos } from '../../utils/conversoes';

const { form, detalhe, editavel, incluiCustos } = useEditor();

/** Aprovado sem a instalação (08B D13): ela fica esmaecida, como os móveis recusados. */
const instalacaoRecusada = computed(() => detalhe.value?.aprovacao?.instalacao_aprovada === false);

/** Preço da instalação calculado pela API (null = sem instalação). */
const preco = computed(() => detalhe.value?.calculo.instalacao?.preco_centavos ?? null);

/** Caixa "Cobrar instalação": marcada quando há custo (mesmo zero). */
const cobrar = computed({
  get: () => form.instalacao_custo_centavos != null,
  set: (marcado: boolean) => { form.instalacao_custo_centavos = marcado ? (form.instalacao_custo_centavos ?? 0) : null; },
});

/** O markup deste orçamento, para a dica do preço ("markup de 90%"). */
const markup = computed(() => (form.markup_bp != null ? formatarBp(form.markup_bp) : null));

/** O campo de dinheiro trabalha em R$; o formulário guarda centavos. */
const custoReais = computed({
  get: () => centavosParaReais(form.instalacao_custo_centavos ?? 0),
  set: (reais: number | null | undefined) => { form.instalacao_custo_centavos = reaisParaCentavos(reais ?? 0); },
});
</script>

<template>
  <div class="flex flex-col gap-4" :class="instalacaoRecusada ? 'opacity-60' : ''" aria-labelledby="titulo-instalacao">
    <div class="flex items-center justify-between gap-3">
      <h3 id="titulo-instalacao" class="flex items-center gap-2 text-sm font-semibold text-zinc-900">
        Instalação
        <BaseStatusPill v-if="instalacaoRecusada" tom="neutro">Não aprovada</BaseStatusPill>
      </h3>
      <!-- Com custos: a chave liga/desliga a cobrança (role="switch": o leitor de tela anuncia o estado). -->
      <button
        v-if="incluiCustos && editavel"
        type="button"
        role="switch"
        :aria-checked="cobrar"
        class="flex shrink-0 items-center gap-2.5 text-sm whitespace-nowrap text-zinc-700 cursor-pointer"
        data-testid="cobrar-instalacao"
        @click="cobrar = !cobrar"
      >
        Cobrar na proposta
        <span :class="['relative h-6 w-10 shrink-0 rounded-full transition-colors', cobrar ? 'bg-brand-primary' : 'bg-zinc-300']">
          <span :class="['absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all', cobrar ? 'left-[1.125rem]' : 'left-0.5']" />
        </span>
      </button>
    </div>

    <!-- Com custos: o custo e o preço que a API calculou. -->
    <template v-if="incluiCustos">
      <div v-if="cobrar" class="grid grid-cols-2 gap-4">
        <MoneyInput v-model="custoReais" label="Custo" :disabled="!editavel" />
        <div>
          <span class="mb-1 block text-xs font-medium text-gray-700">Preço na proposta</span>
          <div class="flex min-h-10 items-center rounded-md border border-zinc-200 bg-zinc-50 px-3 text-sm font-semibold tabular-nums text-zinc-900">
            {{ preco != null ? formatCurrency(preco) : '—' }}
          </div>
        </div>
      </div>
      <p class="text-xs text-zinc-500">
        <template v-if="cobrar">Preço calculado com o markup do orçamento<template v-if="markup"> ({{ markup }})</template>.</template>
        <template v-else>Sem instalação na proposta.</template>
      </p>
    </template>

    <!-- Sem custos: só o preço (D16). -->
    <p v-else class="text-sm text-zinc-600" data-testid="instalacao-so-preco">
      <template v-if="preco != null">
        Instalação incluída: <span class="font-semibold tabular-nums text-zinc-900">{{ formatCurrency(preco) }}</span>
      </template>
      <template v-else>Sem instalação.</template>
    </p>
  </div>
</template>
