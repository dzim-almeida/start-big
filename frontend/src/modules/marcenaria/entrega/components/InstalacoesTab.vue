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
import { AlertTriangle, CalendarDays, CalendarX, MapPin, Printer, Users } from 'lucide-vue-next';

import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseStatusPill, { type TomStatus } from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import type { FilterOption } from '@/shared/types/filter.types';

import { formatTelefone } from '@/shared/utils/document.utils';
import { aguardarImagensDaImpressao, imprimirComPagina } from '@/shared/utils/print.utils';
import { useAbrirOS } from '@/modules/marcenaria/orcamentos/composables/useAbrirOS';

import { useInstalacoes } from '../composables/useInstalacoes';
import type { Instalacao, SituacaoEntrega } from '../schemas/entrega.schema';
import {
  agruparPorDia, datasDoPeriodo, montadoresDaLista, nomesDosMontadores, PERIODOS,
  ROTULO_SITUACAO_ENTREGA, type Periodo,
} from '../utils/entrega';
import ListaDoDiaPrint from './ListaDoDiaPrint.vue';

// --- Filtros (D16) -------------------------------------------------------------------
const periodo = ref<Periodo>('semana');
const soAtrasadas = ref(false);
/** '' = todos os montadores (o <select> nativo não guarda null). */
const montador = ref('');

/** O BaseFilter fala `null` para "Todos"; o filtro guarda ''. */
const montadorSelecionado = computed<string | null>({
  get: () => montador.value || null,
  set: (valor) => { montador.value = valor ?? ''; },
});

const TOM_SITUACAO: Record<SituacaoEntrega, TomStatus> = { PENDENTE: 'neutro', CONFORME: 'sucesso', COM_RESSALVAS: 'alerta' };

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
const opcoesMontador = computed<Record<string, FilterOption>>(() =>
  Object.fromEntries(montadores.value.map((m) => [String(m.funcionario_id), { label: m.nome, class: '', color: 'bg-brand-primary' }])),
);
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
  <div class="space-y-6" data-testid="aba-instalacoes">
    <!-- Filtros: o período, o montador e "Só atrasadas" -->
    <div class="flex flex-wrap items-center gap-4 rounded-2xl border border-zinc-200 bg-white px-6 py-4">
      <div class="flex rounded-xl border border-zinc-200 bg-white p-1 text-xs font-semibold shadow-sm" :class="{ 'opacity-50': soAtrasadas }">
        <button
          v-for="p in PERIODOS"
          :key="p.id"
          type="button"
          class="min-h-9 rounded-lg px-3 md:px-4 cursor-pointer transition-all"
          :class="periodo === p.id ? 'bg-zinc-900 text-white shadow-sm' : 'text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900'"
          :data-testid="`periodo-${p.id}`"
          @click="periodo = p.id; soAtrasadas = false"
        >
          {{ p.rotulo }}
        </button>
      </div>
      <div data-testid="filtro-montador">
        <BaseFilter v-model="montadorSelecionado" :filter-config="opcoesMontador" title="Montador" button-label="Montador" />
      </div>
      <div class="shrink-0" data-testid="so-atrasadas">
        <BaseCheckbox v-model="soAtrasadas" label="Só atrasadas" />
      </div>
    </div>

    <p v-if="isLoading" class="text-sm text-zinc-500">Carregando…</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar as instalações agora.</p>
    <div
      v-else-if="!dias.length"
      class="flex flex-col items-center gap-2 rounded-2xl border border-zinc-200 bg-white px-6 py-12 text-center"
      data-testid="sem-instalacoes"
    >
      <span class="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-zinc-400"><CalendarX :size="22" /></span>
      <p class="text-sm font-medium text-zinc-600">Nenhuma instalação neste período.</p>
      <p class="text-xs text-zinc-500">Agende pela aba Entrega da OS.</p>
    </div>

    <!-- Um bloco por dia ("Segunda, 03/11"), na ordem de data e hora (D16) -->
    <template v-else>
      <section v-for="dia in dias" :key="dia.data" class="overflow-hidden rounded-2xl border border-zinc-200 bg-white" :data-testid="`dia-${dia.data}`">
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 bg-zinc-50 px-6 py-3">
          <strong class="flex items-center gap-2 text-sm font-semibold text-zinc-900">
            <CalendarDays :size="16" class="text-brand-primary" /> {{ dia.titulo }}
            <BaseStatusPill tom="info">{{ dia.itens.length }} {{ dia.itens.length === 1 ? 'instalação' : 'instalações' }}</BaseStatusPill>
          </strong>
          <button type="button" class="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-primary hover:underline cursor-pointer" :data-testid="`imprimir-dia-${dia.data}`" @click="imprimirDia(dia)">
            <Printer :size="14" /> Imprimir a lista do dia
          </button>
        </header>
        <ul class="divide-y divide-zinc-100">
          <li
            v-for="item in dia.itens"
            :key="item.id"
            class="grid grid-cols-1 items-start gap-x-5 gap-y-2 px-6 py-4 text-sm md:grid-cols-[4.5rem_minmax(0,1fr)_minmax(0,14rem)]"
            :data-testid="`instalacao-${item.id}`"
          >
            <span class="flex h-11 w-16 items-center justify-center rounded-lg bg-brand-primary-light font-bold tabular-nums text-brand-primary">
              {{ item.hora_inicio ?? '—' }}
            </span>
            <div class="min-w-0">
              <p class="flex flex-wrap items-center gap-x-1.5 gap-y-1">
                <!-- O número abre a OS direto na aba Entrega -->
                <button
                  type="button"
                  class="font-semibold text-brand-primary hover:underline cursor-pointer disabled:opacity-60"
                  :disabled="abrindo"
                  :data-testid="`abrir-os-${item.id}`"
                  @click="abrirOS(item.numero_os, { abaInicial: 'entrega' })"
                >
                  {{ item.numero_os }}
                </button>
                <span class="font-medium text-zinc-800">· {{ item.cliente ?? '—' }}</span>
                <span v-if="item.telefone" class="text-zinc-500">· {{ formatTelefone(item.telefone) }}</span>
                <span v-if="item.atrasado" data-testid="atrasada">
                  <BaseStatusPill tom="perigo"><AlertTriangle :size="12" /> Atrasada</BaseStatusPill>
                </span>
              </p>
              <p v-if="item.endereco_obra" class="mt-0.5 flex items-center gap-1 text-xs text-zinc-500">
                <MapPin :size="12" class="shrink-0" /> {{ item.endereco_obra }}
              </p>
              <p class="mt-2 flex flex-wrap gap-1.5">
                <BaseStatusPill v-for="ambiente in item.ambientes" :key="ambiente.ambiente_id" :tom="ambiente.situacao ? TOM_SITUACAO[ambiente.situacao] : 'neutro'">
                  {{ ambiente.nome }}<template v-if="ambiente.situacao && ambiente.situacao !== 'PENDENTE'"> · {{ ROTULO_SITUACAO_ENTREGA[ambiente.situacao] }}</template>
                </BaseStatusPill>
              </p>
            </div>
            <p class="flex items-center gap-1.5 text-zinc-600">
              <Users :size="15" class="shrink-0 text-zinc-400" /> {{ nomesDosMontadores(item.montadores) }}
            </p>
          </li>
        </ul>
      </section>
    </template>

    <ListaDoDiaPrint v-if="paraImprimir" :titulo="paraImprimir.titulo" :itens="paraImprimir.itens" />
  </div>
</template>
