<script setup lang="ts">
/**
 * @component InstalacoesTab
 * @description Aba "Instalações" da tela de Serviços (Spec 13B D15-D17; T8a):
 * quem instala onde, por dia, lido de cima para baixo.
 *
 * Atalhos de período (padrão: Esta semana), filtro por montador e "Só
 * atrasadas". O número da OS abre a OS direto na aba Entrega. Cada dia tem
 * "Imprimir a lista do dia" (o roteiro da equipe em papel, P3).
 */
import { computed, nextTick, ref } from 'vue';
import { AlertTriangle, Printer } from 'lucide-vue-next';

import { formatTelefone } from '@/shared/utils/document.utils';
import { aguardarImagensDaImpressao, imprimirComPagina } from '@/shared/utils/print.utils';
import { useAbrirOS } from '@/modules/marcenaria/orcamentos/composables/useAbrirOS';

import { useInstalacoes } from '../composables/useInstalacoes';
import type { Instalacao } from '../schemas/entrega.schema';
import {
  agruparPorDia, CLASSE_SITUACAO_ENTREGA, datasDoPeriodo, montadoresDaLista, nomesDosMontadores, PERIODOS,
  ROTULO_SITUACAO_ENTREGA, type Periodo,
} from '../utils/entrega';
import ListaDoDiaPrint from './ListaDoDiaPrint.vue';

// --- Filtros (D16) -------------------------------------------------------------------
const periodo = ref<Periodo>('semana');
const soAtrasadas = ref(false);
/** '' = todos os montadores (o <select> nativo não guarda null). */
const montador = ref('');

/**
 * O que vai para a API. "Só atrasadas" mostra TODAS as atrasadas, de qualquer
 * dia: um atraso de semana passada também precisa aparecer.
 */
const filtros = computed(() => (soAtrasadas.value
  ? { de: null, ate: null, atrasadas: true }
  : { ...datasDoPeriodo(periodo.value), atrasadas: false }));

const { data: itens, isLoading, isError } = useInstalacoes(filtros);
const { abrirOS, abrindo } = useAbrirOS();

/** Os montadores do período (o filtro não depende do cadastro de funcionários). */
const montadores = computed(() => montadoresDaLista(itens.value ?? []));
const visiveis = computed(() => (itens.value ?? []).filter((item) =>
  !montador.value || item.montadores.some((m) => String(m.funcionario_id) === montador.value)));
const dias = computed(() => agruparPorDia(visiveis.value));

// --- Impressão da lista do dia (D17) -----------------------------------------------------
const LIMPEZA_FORCADA_MS = 2 * 60 * 1000;
const paraImprimir = ref<{ titulo: string; itens: Instalacao[] } | null>(null);

async function imprimirDia(dia: { titulo: string; itens: Instalacao[] }) {
  if (paraImprimir.value) return;
  paraImprimir.value = dia;
  const tituloOriginal = document.title;
  document.title = `Instalações - ${dia.titulo.replace(/\//g, '-')}`;   // nome sugerido do PDF
  await nextTick();
  await aguardarImagensDaImpressao();
  let limpezaForcada: ReturnType<typeof setTimeout> | null = null;
  const restaurar = () => {
    document.title = tituloOriginal;
    paraImprimir.value = null;
    window.removeEventListener('afterprint', restaurar);
    if (limpezaForcada) clearTimeout(limpezaForcada);
  };
  window.addEventListener('afterprint', restaurar);
  limpezaForcada = setTimeout(restaurar, LIMPEZA_FORCADA_MS);
  imprimirComPagina('A4', { folha: 'A4' });
}
</script>

<template>
  <div class="space-y-4" data-testid="aba-instalacoes">
    <!-- Filtros -->
    <div class="flex flex-wrap items-end gap-4">
      <div class="flex rounded-xl border border-zinc-200 bg-white p-1 text-xs font-semibold" :class="{ 'opacity-50': soAtrasadas }">
        <button
          v-for="p in PERIODOS"
          :key="p.id"
          type="button"
          class="rounded-lg px-3 py-1.5 cursor-pointer"
          :class="periodo === p.id ? 'bg-zinc-900 text-white' : 'text-zinc-500 hover:bg-zinc-50'"
          :data-testid="`periodo-${p.id}`"
          @click="periodo = p.id; soAtrasadas = false"
        >
          {{ p.rotulo }}
        </button>
      </div>
      <label class="flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Montador
        <select
          v-model="montador"
          class="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="filtro-montador"
        >
          <option value="">Todos</option>
          <option v-for="m in montadores" :key="m.funcionario_id" :value="String(m.funcionario_id)">{{ m.nome }}</option>
        </select>
      </label>
      <label class="flex items-center gap-2 pb-2 text-sm text-zinc-700">
        <input v-model="soAtrasadas" type="checkbox" class="accent-brand-primary" data-testid="so-atrasadas" />
        Só atrasadas
      </label>
    </div>

    <p v-if="isLoading" class="text-sm text-zinc-400">Carregando…</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar as instalações agora.</p>
    <p v-else-if="!dias.length" class="rounded-xl border border-zinc-200 bg-white px-4 py-6 text-center text-sm text-zinc-500" data-testid="sem-instalacoes">
      Nenhuma instalação neste período.
    </p>

    <!-- Um bloco por dia ("Segunda, 03/11"), na ordem de data e hora (D16) -->
    <template v-else>
      <section v-for="dia in dias" :key="dia.data" class="overflow-hidden rounded-xl border border-zinc-200 bg-white" :data-testid="`dia-${dia.data}`">
        <header class="flex items-center justify-between border-b border-zinc-100 bg-zinc-50 px-4 py-2">
          <strong class="text-sm text-zinc-800">{{ dia.titulo }}</strong>
          <button type="button" class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer" :data-testid="`imprimir-dia-${dia.data}`" @click="imprimirDia(dia)">
            <Printer :size="12" /> Imprimir a lista do dia
          </button>
        </header>
        <ul class="divide-y divide-zinc-100">
          <li v-for="item in dia.itens" :key="item.id" class="flex flex-wrap items-start gap-x-4 gap-y-1 px-4 py-2 text-sm" :data-testid="`instalacao-${item.id}`">
            <span class="w-12 font-semibold tabular-nums text-zinc-800">{{ item.hora_inicio ?? '—' }}</span>
            <div class="min-w-0 flex-1">
              <p>
                <!-- O número abre a OS direto na aba Entrega -->
                <button
                  type="button"
                  class="font-medium text-brand-primary hover:underline cursor-pointer disabled:opacity-60"
                  :disabled="abrindo"
                  :data-testid="`abrir-os-${item.id}`"
                  @click="abrirOS(item.numero_os, { abaInicial: 'entrega' })"
                >
                  {{ item.numero_os }}
                </button>
                <span class="text-zinc-700"> · {{ item.cliente ?? '—' }}</span>
                <span v-if="item.telefone" class="text-zinc-500"> · {{ formatTelefone(item.telefone) }}</span>
                <span
                  v-if="item.atrasado"
                  class="ml-2 inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-700"
                  data-testid="atrasada"
                >
                  <AlertTriangle :size="11" /> Atrasada
                </span>
              </p>
              <p v-if="item.endereco_obra" class="text-xs text-zinc-500">{{ item.endereco_obra }}</p>
              <p class="mt-1 flex flex-wrap gap-1.5">
                <span
                  v-for="ambiente in item.ambientes"
                  :key="ambiente.ambiente_id"
                  class="rounded-full border px-2 py-0.5 text-[11px]"
                  :class="ambiente.situacao ? CLASSE_SITUACAO_ENTREGA[ambiente.situacao] : 'border-zinc-200 text-zinc-500'"
                >
                  {{ ambiente.nome }}<template v-if="ambiente.situacao && ambiente.situacao !== 'PENDENTE'"> · {{ ROTULO_SITUACAO_ENTREGA[ambiente.situacao] }}</template>
                </span>
              </p>
            </div>
            <span class="text-zinc-600">{{ nomesDosMontadores(item.montadores) }}</span>
          </li>
        </ul>
      </section>
    </template>

    <ListaDoDiaPrint v-if="paraImprimir" :titulo="paraImprimir.titulo" :itens="paraImprimir.itens" />
  </div>
</template>
