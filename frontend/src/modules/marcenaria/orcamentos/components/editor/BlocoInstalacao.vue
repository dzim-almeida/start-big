<script setup lang="ts">
/**
 * @component BlocoInstalacao
 * @description Instalação do orçamento (Spec 06B §6.2, D16; SPEC-00 C3).
 *
 * - Quem vê custos: caixa "Cobrar instalação" + custo; o PREÇO vem da API.
 *   Caixa desmarcada manda `instalacao_custo_centavos = null` (sem a linha).
 * - Quem não vê custos: só o preço (o custo nem chega na resposta).
 */
import { computed } from 'vue';

import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useEditor } from '../../composables/useEditorContexto';
import { centavosParaReais, reaisParaCentavos } from '../../utils/conversoes';

const { form, detalhe, editavel, incluiCustos } = useEditor();

/** Preço da instalação calculado pela API (null = sem instalação). */
const preco = computed(() => detalhe.value?.calculo.instalacao?.preco_centavos ?? null);

/** Caixa "Cobrar instalação": marcada quando há custo (mesmo zero). */
const cobrar = computed({
  get: () => form.instalacao_custo_centavos != null,
  set: (marcado: boolean) => { form.instalacao_custo_centavos = marcado ? (form.instalacao_custo_centavos ?? 0) : null; },
});

/** O campo de dinheiro trabalha em R$; o formulário guarda centavos. */
const custoReais = computed({
  get: () => centavosParaReais(form.instalacao_custo_centavos ?? 0),
  set: (reais: number | null | undefined) => { form.instalacao_custo_centavos = reaisParaCentavos(reais ?? 0); },
});
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-instalacao">
    <h2 id="titulo-instalacao" class="mb-3 text-sm font-bold text-zinc-800">Instalação</h2>

    <!-- Com custos: liga/desliga e informa o custo; o preço vem pronto. -->
    <div v-if="incluiCustos" class="flex flex-wrap items-end gap-6">
      <BaseCheckbox v-model="cobrar" label="Cobrar instalação" :disabled="!editavel" />
      <div v-if="cobrar" class="w-40">
        <MoneyInput v-model="custoReais" label="Custo" :disabled="!editavel" />
      </div>
      <p v-if="cobrar" class="text-sm text-zinc-600">
        Preço <span class="font-semibold tabular-nums text-zinc-800">{{ preco != null ? formatCurrency(preco) : '—' }}</span>
      </p>
    </div>

    <!-- Sem custos: só o preço (D16). -->
    <p v-else class="text-sm text-zinc-600" data-testid="instalacao-so-preco">
      <template v-if="preco != null">
        Instalação incluída: <span class="font-semibold tabular-nums text-zinc-800">{{ formatCurrency(preco) }}</span>
      </template>
      <template v-else>Sem instalação.</template>
    </p>
  </section>
</template>
