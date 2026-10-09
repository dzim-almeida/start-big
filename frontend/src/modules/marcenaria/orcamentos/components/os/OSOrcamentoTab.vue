<script setup lang="ts">
/**
 * @component OSOrcamentoTab
 * @description Aba "Orçamento" do modal de OS (Spec 08B D19-D23, §6.2): o
 * que foi vendido, para quem trabalha na OS, sem abrir outro módulo.
 *
 * Só leitura e NUNCA com custo (08A Revisão 1): o lugar de ver margem é o
 * orçamento (link "Abrir orçamento"). Não conhece o modal de OS: avisa o pai
 * por eventos ("preencher adiantamento", "abrir orçamento").
 */
import { computed, toRef } from 'vue';
import { AlertTriangle, ExternalLink } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatData } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';

import { useOrcamentoDaOS } from '../../composables/useOrcamentoDaOS';
import { formatarMedidas } from '../../utils/conversoes';

const props = defineProps<{
  numeroOs: string;
  /** Total atual da OS (pode divergir do aprovado de propósito: D22). */
  totalOsCentavos: number | null;
}>();

const emit = defineEmits<{
  /** Coloca no campo Adiantamento o valor do sinal combinado (o usuário escolhe a forma e salva, D21). */
  preencherAdiantamento: [valorCentavos: number];
  abrirOrcamento: [orcamentoId: number];
}>();

const { data: resumo, isLoading, isError, semOrcamento } = useOrcamentoDaOS(toRef(props, 'numeroOs'));

/** Quanto do sinal combinado ainda não entrou na OS (D21). */
const sinalFaltando = computed(() => {
  const r = resumo.value;
  if (!r?.sinal_combinado_centavos) return 0;
  return Math.max(0, r.sinal_combinado_centavos - r.sinal_recebido_centavos);
});

/** O total da OS mudou depois da aprovação (desconto, item manual, frete): D22. */
const totalDiferente = computed(() =>
  resumo.value?.total_aprovado_centavos != null
  && props.totalOsCentavos != null
  && resumo.value.total_aprovado_centavos !== props.totalOsCentavos,
);
</script>

<template>
  <div class="space-y-4" data-testid="aba-orcamento">
    <p v-if="isLoading" class="text-sm text-zinc-400">Carregando orçamento…</p>
    <p v-else-if="semOrcamento" class="text-sm text-zinc-500" data-testid="sem-orcamento">Esta OS não foi gerada por um orçamento.</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar o orçamento desta OS.</p>

    <template v-else-if="resumo">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-base font-bold text-zinc-800">Orçamento {{ resumo.codigo }} v{{ resumo.versao }}</p>
          <p class="text-xs text-zinc-500">
            Aprovado em {{ formatData(resumo.data_aprovacao) }}<template v-if="resumo.aprovado_por"> por {{ resumo.aprovado_por }}</template>
            <template v-if="resumo.projeto"> · {{ resumo.projeto }}</template>
          </p>
        </div>
        <BaseButton variant="secondary" size="sm" data-testid="abrir-orcamento" @click="emit('abrirOrcamento', resumo.orcamento_id)">
          <ExternalLink :size="14" class="mr-1" /> Abrir orçamento
        </BaseButton>
      </div>

      <div class="rounded-xl border border-zinc-200">
        <div class="flex items-center justify-between border-b border-zinc-100 px-4 py-2 text-xs">
          <span class="font-semibold text-zinc-700">Móveis aprovados ({{ resumo.moveis.length }})</span>
          <span v-if="resumo.moveis_nao_aprovados" class="text-zinc-400">
            {{ resumo.moveis_nao_aprovados }} {{ resumo.moveis_nao_aprovados === 1 ? 'móvel não aprovado' : 'móveis não aprovados' }}
          </span>
        </div>
        <ul class="divide-y divide-zinc-100 text-sm">
          <li v-for="(movel, indice) in resumo.moveis" :key="indice" class="flex flex-wrap items-center gap-x-4 px-4 py-2">
            <span class="min-w-40 flex-1 font-medium text-zinc-800">{{ movel.nome }}</span>
            <span class="text-xs text-zinc-500">{{ movel.ambiente }}</span>
            <span class="text-xs text-zinc-500">{{ formatarMedidas(movel.medidas.largura_mm, movel.medidas.altura_mm, movel.medidas.profundidade_mm) }}</span>
            <span class="text-xs text-zinc-600">{{ movel.quantidade }}×</span>
          </li>
          <li v-if="resumo.instalacao_aprovada" class="px-4 py-2 font-medium text-zinc-800">Instalação e montagem</li>
        </ul>
      </div>

      <p class="text-sm text-zinc-700">
        Total aprovado <strong class="tabular-nums">{{ formatCurrency(resumo.total_aprovado_centavos ?? 0) }}</strong>
      </p>
      <p v-if="totalDiferente" class="text-xs text-zinc-500" data-testid="totais-diferentes">
        Total aprovado no orçamento: {{ formatCurrency(resumo.total_aprovado_centavos ?? 0) }} · total atual da OS: {{ formatCurrency(totalOsCentavos ?? 0) }}
      </p>

      <!-- D21: o sinal que ainda não entrou; o lugar de lançar é o Adiantamento da OS. -->
      <div
        v-if="sinalFaltando > 0"
        class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
        data-testid="aviso-sinal"
      >
        <span class="flex items-center gap-2">
          <AlertTriangle :size="16" />
          Sinal combinado {{ formatCurrency(resumo.sinal_combinado_centavos ?? 0) }} — recebido {{ formatCurrency(resumo.sinal_recebido_centavos) }}.
        </span>
        <BaseButton variant="secondary" size="sm" data-testid="preencher-adiantamento" @click="emit('preencherAdiantamento', resumo.sinal_combinado_centavos ?? 0)">
          Preencher adiantamento
        </BaseButton>
      </div>
    </template>
  </div>
</template>
