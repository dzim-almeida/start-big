<script setup lang="ts">
/**
 * @component OSMarcenariaCabecalho
 * @description Topo do modal de OS da marcenaria (redesign 10/2026): número,
 * situação, prioridade e de onde a OS veio — o orçamento aprovado (link),
 * o código do projeto e a data de criação.
 *
 * O orçamento de origem vem do mesmo resumo da aba "Orçamento"
 * (useOrcamentoDaOS, mesma chave de cache: abrir a aba não busca de novo).
 */
import { computed, toRef } from 'vue';
import { Hammer, X } from 'lucide-vue-next';

import BaseStatusPill, { type TomStatus } from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import { formatData, formatHora } from '@/shared/utils/date.utils';
import { useOrcamentoDaOS } from '@/modules/marcenaria/orcamentos/composables/useOrcamentoDaOS';

const props = defineProps<{
  numeroOs: string | null;
  /** Rótulo da situação no vocabulário do segmento ("Em Produção"). */
  rotuloStatus: string;
  status?: string | null;
  prioridade?: string | null;
  /** Código do projeto (PRJ-…), o nº de série do objeto. */
  projeto?: string | null;
  dataCriacao?: string | null;
}>();

const emit = defineEmits<{ close: []; abrirOrcamento: [id: number] }>();

const { data: orcamento } = useOrcamentoDaOS(toRef(props, 'numeroOs'));

const tomStatus = computed<TomStatus>(() => {
  switch (props.status) {
    case 'FINALIZADA': return 'sucesso';
    case 'CANCELADA': return 'perigo';
    case 'AGUARDANDO_PECAS': return 'alerta';
    default: return 'info';
  }
});

/** Só a prioridade que pede atenção ganha etiqueta (Normal/Baixa é o comum). */
const prioridadeVisivel = computed(() => {
  if (props.prioridade === 'URGENTE') return { tom: 'perigo' as const, texto: 'Urgente' };
  if (props.prioridade === 'ALTA') return { tom: 'alerta' as const, texto: 'Prioridade alta' };
  return null;
});

/** O banco guarda em UTC sem fuso: a conversão é a do date.utils (C19), nunca `new Date()` cru. */
const criadaEm = computed(() =>
  props.dataCriacao ? `${formatData(props.dataCriacao)} às ${formatHora(props.dataCriacao)}` : null,
);
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-200 px-6 py-4" data-testid="cabecalho-os-marcenaria">
    <div class="flex min-w-0 items-center gap-3.5">
      <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-primary text-white" aria-hidden="true">
        <Hammer :size="22" />
      </span>
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-2">
          <h2 class="text-xl font-bold text-zinc-900">{{ numeroOs ?? 'Ordem de Serviço' }}</h2>
          <BaseStatusPill :tom="tomStatus">{{ rotuloStatus }}</BaseStatusPill>
          <BaseStatusPill v-if="prioridadeVisivel" :tom="prioridadeVisivel.tom">{{ prioridadeVisivel.texto }}</BaseStatusPill>
        </div>
        <p class="flex flex-wrap items-center gap-x-1.5 text-xs text-zinc-500">
          <template v-if="orcamento">
            Origem:
            <button
              type="button"
              class="font-medium text-brand-primary hover:underline cursor-pointer"
              data-testid="origem-orcamento"
              @click="emit('abrirOrcamento', orcamento.orcamento_id)"
            >
              Orçamento {{ orcamento.codigo }}
            </button>
            <span aria-hidden="true">·</span>
          </template>
          <template v-if="projeto">Projeto {{ projeto }} <span aria-hidden="true">·</span></template>
          <template v-if="criadaEm">Criada em {{ criadaEm }}</template>
        </p>
      </div>
    </div>

    <button
      type="button"
      class="flex h-11 w-11 items-center justify-center rounded-lg text-zinc-500 hover:bg-red-50 hover:text-red-600 cursor-pointer"
      aria-label="Fechar OS"
      @click="emit('close')"
    >
      <X :size="20" />
    </button>
  </div>
</template>
