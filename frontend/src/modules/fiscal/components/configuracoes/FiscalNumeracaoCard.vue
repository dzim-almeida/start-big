<script setup lang="ts">
/**
 * Buracos na numeração e o histórico de inutilizações.
 *
 * Todo número reservado que não virou nota autorizada é um buraco, e a SEFAZ
 * exige que ele seja declarado. Este cartão é a única porta para isso na
 * tela: até 19/09/2026 os três endpoints existiam e nenhum era chamado.
 */
import { computed, ref } from 'vue';
import { AlertTriangle, Ban, CheckCircle, CircleDashed, Clock, HelpCircle, Hash, XCircle } from 'lucide-vue-next';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { formatDataHora } from '@/shared/utils/date.utils';

import {
  useFiscalGapsNumeracaoQuery,
  useFiscalInutilizacoesQuery,
} from '../../composables/useFiscalNumeracaoQuery';
import { avisoViradaDeAno } from '../../utils/numeracao.utils';
import type { GapNumeracao, InutilizacaoRead } from '../../types/fiscal.types';
import FiscalInutilizarModal from './FiscalInutilizarModal.vue';

const { data: gaps, isLoading: carregandoGaps } = useFiscalGapsNumeracaoQuery();
const { data: inutilizacoes } = useFiscalInutilizacoesQuery();

const aviso = computed(() => avisoViradaDeAno());

const modalAberto = ref(false);
const gapEscolhido = ref<GapNumeracao | null>(null);

function abrir(gap: GapNumeracao) {
  gapEscolhido.value = gap;
  modalAberto.value = true;
}

function faixa(i: Pick<InutilizacaoRead, 'numero_inicial' | 'numero_final'>): string {
  return i.numero_inicial === i.numero_final
    ? `nº ${i.numero_inicial}`
    : `nº ${i.numero_inicial}–${i.numero_final}`;
}

/**
 * Um rótulo e uma cor por status. Os três "não" são diferentes de propósito:
 * quem lê precisa saber se foi a SEFAZ, a plataforma, ou ninguém que respondeu.
 */
const STATUS = {
  HOMOLOGADA: { rotulo: 'Homologada', icone: CheckCircle, cor: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  PROCESSANDO: { rotulo: 'Aguardando SEFAZ', icone: Clock, cor: 'text-blue-700 bg-blue-50 border-blue-200' },
  PENDENTE: { rotulo: 'Aguardando SEFAZ', icone: Clock, cor: 'text-blue-700 bg-blue-50 border-blue-200' },
  REJEITADA: { rotulo: 'Recusada pela SEFAZ', icone: XCircle, cor: 'text-rose-700 bg-rose-50 border-rose-200' },
  NAO_TRANSMITIDA: { rotulo: 'Não chegou à SEFAZ', icone: CircleDashed, cor: 'text-amber-700 bg-amber-50 border-amber-200' },
  INDETERMINADA: { rotulo: 'Sem resposta', icone: HelpCircle, cor: 'text-zinc-600 bg-zinc-100 border-zinc-200' },
} as const;

function statusDe(i: InutilizacaoRead) {
  return STATUS[i.status as keyof typeof STATUS] ?? STATUS.INDETERMINADA;
}

const historico = computed(() => (inutilizacoes.value ?? []).slice(0, 8));
</script>

<template>
  <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-10 h-10 bg-brand-primary-light rounded-xl flex items-center justify-center text-brand-primary">
        <LucideIcon :icon="Hash" />
      </div>
      <div>
        <h3 class="text-base font-bold text-zinc-900">Numeração e Inutilização</h3>
        <p class="text-xs text-zinc-500">Números reservados que não viraram nota precisam ser declarados à SEFAZ</p>
      </div>
    </div>

    <!-- O lembrete de virada de ano só aparece em dezembro e janeiro. -->
    <div
      v-if="aviso"
      class="mb-4 flex gap-2.5 rounded-xl border p-3 text-xs"
      :class="aviso.nivel === 'alerta'
        ? 'border-rose-200 bg-rose-50 text-rose-800'
        : 'border-amber-200 bg-amber-50 text-amber-800'"
    >
      <LucideIcon :icon="AlertTriangle" class="w-4 h-4 shrink-0 mt-0.5" />
      <div>
        <p class="font-semibold">{{ aviso.titulo }}</p>
        <p class="mt-0.5 opacity-90">{{ aviso.detalhe }}</p>
      </div>
    </div>

    <!-- Buracos -->
    <div class="mb-5">
      <p class="text-[11px] font-medium text-zinc-400 mb-2 uppercase tracking-wide">Buracos na numeração</p>

      <p v-if="carregandoGaps" class="text-xs text-zinc-400">Conferindo a sequência…</p>

      <p
        v-else-if="!gaps?.length"
        class="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-xl px-3 py-2"
      >
        <LucideIcon :icon="CheckCircle" class="w-3.5 h-3.5" /> Sequência sem buracos.
      </p>

      <ul v-else class="flex flex-col divide-y divide-zinc-100 rounded-xl border border-zinc-100">
        <li
          v-for="gap in gaps"
          :key="`${gap.serie}-${gap.numero_inicial}`"
          class="flex items-center justify-between gap-3 px-3 py-2.5"
        >
          <div class="min-w-0">
            <p class="text-sm font-semibold text-zinc-800">
              Série {{ gap.serie }} · {{ faixa(gap) }}
            </p>
            <p class="text-xs text-zinc-500">
              {{ gap.quantidade === 1 ? '1 número' : `${gap.quantidade} números` }} sem nota
            </p>
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs font-semibold text-amber-800 cursor-pointer hover:bg-amber-100"
            @click="abrir(gap)"
          >
            <LucideIcon :icon="Ban" class="w-3.5 h-3.5" /> Inutilizar
          </button>
        </li>
      </ul>
    </div>

    <!-- Histórico -->
    <div v-if="historico.length">
      <p class="text-[11px] font-medium text-zinc-400 mb-2 uppercase tracking-wide">Últimos pedidos</p>
      <ul class="flex flex-col divide-y divide-zinc-100">
        <li
          v-for="i in historico"
          :key="i.id"
          class="flex flex-wrap items-start justify-between gap-2 py-2"
        >
          <div class="min-w-0">
            <p class="text-sm text-zinc-800">
              Série {{ i.serie }} · {{ faixa(i) }}
              <span class="text-zinc-400">· {{ i.ano }}</span>
            </p>
            <p class="text-xs text-zinc-500">
              {{ i.data_solicitacao ? formatDataHora(i.data_solicitacao) : '' }}
              <template v-if="i.protocolo"> · Protocolo {{ i.protocolo }}</template>
            </p>
            <p
              v-if="i.mensagem_sefaz && i.status !== 'HOMOLOGADA'"
              class="mt-0.5 text-xs text-zinc-500"
            >
              {{ i.mensagem_sefaz }}
            </p>
          </div>
          <span
            class="inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold"
            :class="statusDe(i).cor"
          >
            <LucideIcon :icon="statusDe(i).icone" class="w-3 h-3" />
            {{ statusDe(i).rotulo }}
          </span>
        </li>
      </ul>
    </div>

    <FiscalInutilizarModal v-model:is-open="modalAberto" :gap="gapEscolhido" />
  </div>
</template>
