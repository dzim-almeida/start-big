<script setup lang="ts">
/**
 * @component PatioTab
 * @description O pátio do lava-rápido: a tela inicial de Serviços no segmento
 * (Spec 04B, SPEC-00 U1/U3).
 *
 * Três colunas — Aguardando, Lavando, Pronto — e as entregas do dia
 * recolhidas embaixo. Cada cartão é uma OS de sempre: "Ver detalhes" abre o
 * modal de OS, e "Receber" abre esse modal já no recebimento (pagamento,
 * caixa e comissão continuam num lugar só).
 */
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { CarFront, CheckCircle2, ChevronDown, Clock, Droplets } from 'lucide-vue-next';

import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import { useOSCreateFlow } from '@/modules/order-service/ordens/composables/useOSCreateFlow';
import { getUniqueOS } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { useRotulosStatusOS } from '@/modules/order-service/shared/segmento/useRotulosStatusOS';
import { useToast } from '@/shared/composables/useToast';

import type { CartaoPatio } from '../../shared/schemas/patio.schema';
import { reais } from '../../shared/utils/lavaRapido';
import { usePatioMutations, usePatioQuery } from '../composables/usePatio';
import CartaoVeiculo from './CartaoVeiculo.vue';
import LavadoresModal from './LavadoresModal.vue';

const { data: patio, isLoading, isError } = usePatioQuery();
const { avancar, voltar, trocarLavadores, recarregar } = usePatioMutations();
const { openExistingOS, isFormModalOpen } = useOSCreateFlow();
const { rotuloStatus } = useRotulosStatusOS();
const toast = useToast();

// Relógio da tela: o "há X min" anda sozinho, sem recarregar o pátio.
const agora = ref(new Date());
const relogio = setInterval(() => { agora.value = new Date(); }, 30_000);
onBeforeUnmount(() => clearInterval(relogio));

// Fechou o modal de OS (recebeu, editou, cancelou): o pátio reflete na hora.
watch(isFormModalOpen, (aberto) => { if (!aberto) recarregar(); });

const colunas = computed(() => [
  { id: 'aguardando' as const, titulo: rotuloStatus('ABERTA'), itens: patio.value?.aguardando ?? [], cor: 'bg-blue-500' },
  { id: 'lavando' as const, titulo: rotuloStatus('EM_ANDAMENTO'), itens: patio.value?.lavando ?? [], cor: 'bg-amber-500' },
  { id: 'pronto' as const, titulo: rotuloStatus('AGUARDANDO_RETIRADA'), itens: patio.value?.pronto ?? [], cor: 'bg-emerald-500' },
]);

const entregues = computed(() => patio.value?.entregues_hoje ?? []);
const verEntregues = ref(false);

const indicadores = computed(() => ({
  noPatio: colunas.value.reduce((n, c) => n + c.itens.length, 0),
  lavando: patio.value?.lavando.length ?? 0,
  prontos: patio.value?.pronto.length ?? 0,
  faturadoHoje: entregues.value.reduce((soma, c) => soma + c.valor_total, 0),
}));

// --- Ações -----------------------------------------------------------------------------
const ocupado = computed(() => avancar.isPending.value || voltar.isPending.value);

async function abrirOS(numeroOs: string, receber = false) {
  try {
    openExistingOS(await getUniqueOS(numeroOs), false, { receber });
  } catch {
    toast.error('Não foi possível abrir a OS.');
  }
}

const cartaoLavadores = ref<CartaoPatio | null>(null);
function salvarLavadores(ids: number[]) {
  if (!cartaoLavadores.value) return;
  trocarLavadores.mutate(
    { numeroOs: cartaoLavadores.value.numero_os, ids },
    { onSuccess: () => { cartaoLavadores.value = null; } },
  );
}
</script>

<template>
  <div class="space-y-6" data-testid="patio">
    <div class="grid grid-cols-2 gap-2 md:gap-6 lg:grid-cols-4">
      <BaseStatsCard :icon="CarFront" label="No pátio" :value="String(indicadores.noPatio)" />
      <BaseStatsCard :icon="Droplets" label="Lavando agora" :value="String(indicadores.lavando)" />
      <BaseStatsCard
        :icon="Clock"
        label="Prontos esperando"
        :value="String(indicadores.prontos)"
        :tone="indicadores.prontos ? 'alerta' : 'neutro'"
      />
      <BaseStatsCard :icon="CheckCircle2" label="Recebido hoje" :value="reais(indicadores.faturadoHoje)" />
    </div>

    <p v-if="isError" class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      Não foi possível carregar o pátio agora. Ele tenta de novo sozinho.
    </p>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <section
        v-for="coluna in colunas"
        :key="coluna.id"
        class="flex min-h-64 flex-col gap-3 rounded-3xl bg-zinc-100/70 p-3"
        :data-testid="`coluna-${coluna.id}`"
      >
        <header class="flex items-center gap-2 px-1">
          <span class="h-2.5 w-2.5 rounded-full" :class="coluna.cor" />
          <h3 class="text-sm font-bold uppercase tracking-wide text-zinc-700">{{ coluna.titulo }}</h3>
          <span class="ml-auto rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-zinc-500">
            {{ coluna.itens.length }}
          </span>
        </header>

        <p v-if="isLoading" class="px-1 text-sm text-zinc-400">Carregando…</p>
        <p v-else-if="!coluna.itens.length" class="px-1 py-6 text-center text-sm text-zinc-400">Nenhum veículo.</p>

        <CartaoVeiculo
          v-for="cartao in coluna.itens"
          :key="cartao.numero_os"
          :cartao="cartao"
          :coluna="coluna.id"
          :agora="agora"
          :ocupado="ocupado"
          @avancar="avancar.mutate"
          @voltar="voltar.mutate"
          @receber="abrirOS($event, true)"
          @detalhes="abrirOS($event)"
          @lavadores="cartaoLavadores = $event"
        />
      </section>
    </div>

    <!-- Entregues hoje, recolhido -->
    <section class="rounded-3xl border border-zinc-200 bg-white">
      <button
        type="button"
        class="flex w-full items-center gap-2 px-5 py-4 text-left"
        @click="verEntregues = !verEntregues"
      >
        <CheckCircle2 :size="16" class="text-emerald-600" />
        <span class="text-sm font-semibold text-zinc-800">Entregues hoje ({{ entregues.length }})</span>
        <ChevronDown :size="16" class="ml-auto text-zinc-400 transition-transform" :class="verEntregues && 'rotate-180'" />
      </button>
      <div v-if="verEntregues" class="grid grid-cols-1 gap-3 border-t border-zinc-100 p-4 md:grid-cols-2 lg:grid-cols-3">
        <p v-if="!entregues.length" class="text-sm text-zinc-400">Nenhuma entrega ainda hoje.</p>
        <CartaoVeiculo
          v-for="cartao in entregues"
          :key="cartao.numero_os"
          :cartao="cartao"
          coluna="entregue"
          :agora="agora"
          @detalhes="abrirOS($event)"
        />
      </div>
    </section>

    <LavadoresModal
      :cartao="cartaoLavadores"
      :salvando="trocarLavadores.isPending.value"
      @close="cartaoLavadores = null"
      @salvar="salvarLavadores"
    />
  </div>
</template>
