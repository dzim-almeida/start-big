<script setup lang="ts">
/**
 * @component OSOrcamentoTab
 * @description Aba "Orçamento" do modal de OS (Spec 08B D19-D23, §6.2): o
 * que foi vendido, para quem trabalha na OS, sem abrir outro módulo.
 *
 * Só leitura e NUNCA com custo (08A Revisão 1): o lugar de ver margem é o
 * orçamento (link "Abrir orçamento"). Não conhece o modal de OS: avisa o pai
 * por eventos ("preencher adiantamento", "abrir orçamento").
 *
 * ADITIVOS (remodelação item 20): móveis a mais para esta OS. A aba lista os
 * aditivos (com status e total) e o botão "Novo aditivo" cria um já com o
 * cliente e o projeto da OS e abre o editor dele. Aprovado, ele soma aqui.
 */
import { computed, ref, toRef } from 'vue';
import { AlertTriangle, ExternalLink, FilePlus2, FileText } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useToast } from '@/shared/composables/useToast';
import { formatData } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';

import OrcamentoStatusBadge from '../lista/OrcamentoStatusBadge.vue';
import { useOrcamentoDaOS } from '../../composables/useOrcamentoDaOS';
import { usePermissoesOrcamento } from '../../composables/usePermissoesOrcamento';
import type { StatusOrcamento } from '../../constants/orcamento.constants';
import { criarAditivo } from '../../services/aprovacao.service';
import { formatarMedidas } from '../../utils/conversoes';
import { mensagemDoErro } from '../../utils/erros';

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

/**
 * Total aprovado da OS: o do orçamento + o dos aditivos aprovados (item 20).
 * Backend antigo (sem o campo): só o do orçamento, como antes.
 */
const totalAprovado = computed(() => resumo.value?.total_geral_aprovado_centavos ?? resumo.value?.total_aprovado_centavos ?? null);

/** O total da OS mudou depois da aprovação (desconto, item manual, frete): D22. */
const totalDiferente = computed(() =>
  totalAprovado.value != null
  && props.totalOsCentavos != null
  && totalAprovado.value !== props.totalOsCentavos,
);

// --- Aditivos (remodelação item 20) -----------------------------------------------------
const toast = useToast();
const { podeGerir } = usePermissoesOrcamento();
const criandoAditivo = ref(false);
/** "Novo aditivo": só com o orçamento aprovado, a OS aberta (o backend diz) e permissão. */
const podeCriarAditivo = computed(() => !!resumo.value?.pode_criar_aditivo && podeGerir.value);

/** Cria o aditivo (rascunho, sem móveis) e abre o editor dele para incluir os móveis. */
async function novoAditivo() {
  criandoAditivo.value = true;
  try {
    const aditivo = await criarAditivo(props.numeroOs);
    emit('abrirOrcamento', aditivo.id);                  // o pai fecha a OS e abre o editor
  } catch (erro) {
    toast.error('Não foi possível criar o aditivo.', mensagemDoErro(erro));
  } finally {
    criandoAditivo.value = false;
  }
}
</script>

<template>
  <div class="flex flex-col gap-6" data-testid="aba-orcamento">
    <p v-if="isLoading" class="text-sm text-zinc-500">Carregando orçamento…</p>
    <p v-else-if="semOrcamento" class="text-sm text-zinc-500" data-testid="sem-orcamento">Esta OS não foi gerada por um orçamento.</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar o orçamento desta OS.</p>

    <template v-else-if="resumo">
      <div class="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-zinc-200 bg-white px-6 py-5">
        <div class="flex items-center gap-3.5">
          <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-primary text-white" aria-hidden="true"><FileText :size="22" /></span>
          <div>
          <p class="text-base font-semibold text-zinc-900">Orçamento {{ resumo.codigo }} v{{ resumo.versao }}</p>
          <p class="text-xs text-zinc-500">
            Aprovado em {{ formatData(resumo.data_aprovacao) }}<template v-if="resumo.aprovado_por"> por {{ resumo.aprovado_por }}</template>
            <template v-if="resumo.projeto"> · {{ resumo.projeto }}</template>
          </p>
          </div>
        </div>
        <BaseButton variant="secondary" size="sm" data-testid="abrir-orcamento" @click="emit('abrirOrcamento', resumo.orcamento_id)">
          <ExternalLink :size="14" class="mr-1" /> Abrir orçamento
        </BaseButton>
      </div>

      <div class="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <div class="flex items-center justify-between border-b border-zinc-100 bg-zinc-50 px-6 py-3 text-xs">
          <span class="font-semibold uppercase tracking-wide text-zinc-600">Móveis aprovados ({{ resumo.moveis.length }})</span>
          <span v-if="resumo.moveis_nao_aprovados" class="text-zinc-400">
            {{ resumo.moveis_nao_aprovados }} {{ resumo.moveis_nao_aprovados === 1 ? 'móvel não aprovado' : 'móveis não aprovados' }}
          </span>
        </div>
        <ul class="divide-y divide-zinc-100 text-sm">
          <li v-for="(movel, indice) in resumo.moveis" :key="indice" class="flex flex-wrap items-center gap-x-4 px-6 py-3">
            <span class="min-w-40 flex-1 font-medium text-zinc-800">{{ movel.nome }}</span>
            <span class="text-xs text-zinc-500">{{ movel.ambiente }}</span>
            <span class="text-xs text-zinc-500">{{ formatarMedidas(movel.medidas.largura_mm, movel.medidas.altura_mm, movel.medidas.profundidade_mm) }}</span>
            <span class="text-xs text-zinc-600">{{ movel.quantidade }}×</span>
          </li>
          <li v-if="resumo.instalacao_aprovada" class="px-6 py-3 font-medium text-zinc-800">Instalação e montagem</li>
        </ul>
      </div>

      <!-- Aditivos (remodelação item 20): móveis a mais para esta mesma OS -->
      <section class="rounded-2xl border border-zinc-200 bg-white" data-testid="aditivos">
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 px-6 py-3.5">
          <div>
            <h3 class="text-sm font-semibold text-zinc-900">Aditivos</h3>
            <p class="text-xs text-zinc-500">Móveis a mais para esta obra. Aprovado, o aditivo soma nesta OS.</p>
          </div>
          <BaseButton
            v-if="podeCriarAditivo"
            variant="primary"
            size="sm"
            :is-loading="criandoAditivo"
            data-testid="novo-aditivo"
            @click="novoAditivo"
          >
            <FilePlus2 :size="14" class="mr-1" /> Novo aditivo
          </BaseButton>
        </header>
        <p v-if="!resumo.aditivos.length" class="px-6 py-4 text-sm text-zinc-500" data-testid="sem-aditivos">Nenhum aditivo.</p>
        <ul v-else class="divide-y divide-zinc-100 text-sm">
          <li v-for="aditivo in resumo.aditivos" :key="aditivo.orcamento_id" class="px-6 py-3" :data-testid="`aditivo-${aditivo.orcamento_id}`">
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span class="font-semibold text-zinc-800">{{ aditivo.codigo }}<template v-if="aditivo.versao > 1"> v{{ aditivo.versao }}</template></span>
              <OrcamentoStatusBadge :status="aditivo.status as StatusOrcamento" />
              <span class="text-xs text-zinc-500">
                {{ aditivo.moveis.length }} {{ aditivo.moveis.length === 1 ? 'móvel' : 'móveis' }}
                <template v-if="aditivo.moveis.length"> · {{ aditivo.moveis.map((m) => m.nome).join(', ') }}</template>
              </span>
              <span class="ml-auto tabular-nums font-semibold text-zinc-800">
                {{ formatCurrency(aditivo.total_aprovado_centavos ?? aditivo.total_centavos) }}
              </span>
              <BaseButton variant="secondary" size="sm" :data-testid="`abrir-aditivo-${aditivo.orcamento_id}`" @click="emit('abrirOrcamento', aditivo.orcamento_id)">
                <ExternalLink :size="14" class="mr-1" /> Abrir
              </BaseButton>
            </div>
          </li>
        </ul>
      </section>

      <p class="text-sm text-zinc-700">
        Total aprovado <strong class="tabular-nums" data-testid="total-aprovado">{{ formatCurrency(totalAprovado ?? 0) }}</strong>
        <span v-if="resumo.aditivos.some((a) => a.status === 'APROVADO')" class="text-xs text-zinc-500"> (orçamento + aditivos aprovados)</span>
      </p>
      <p v-if="totalDiferente" class="text-xs text-zinc-500" data-testid="totais-diferentes">
        Total aprovado: {{ formatCurrency(totalAprovado ?? 0) }} · total atual da OS: {{ formatCurrency(totalOsCentavos ?? 0) }}
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
