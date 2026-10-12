<script setup lang="ts">
/**
 * @component QuadroProducaoTab
 * @description O quadro da fábrica: aba "Produção" da tela de Serviços
 * (Spec 12B D15-D18).
 *
 * Uma linha por OS aberta, na ordem da PREVISÃO (a mais próxima primeiro: é
 * a ordem de prioridade da fábrica), com o progresso e o que vem a seguir.
 * O número abre a OS direto na aba Produção. Recarrega a cada 30 s.
 */
import { computed, ref } from 'vue';
import { AlertTriangle, CalendarClock, CheckCircle2, Hammer } from 'lucide-vue-next';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseStatsCard from '@/shared/components/layout/StatsCard/BaseStatsCard.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseProgressBar from '@/shared/components/ui/BaseProgressBar/BaseProgressBar.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseStatusPill, { type TomStatus } from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import type { FilterOption } from '@/shared/types/filter.types';

import { useAbrirOS } from '@/modules/marcenaria/orcamentos/composables/useAbrirOS';

import { useQuadroProducao } from '../composables/useQuadroProducao';
import type { ItemQuadro } from '../schemas/producao.schema';
import { diaMes, prazoDaEntrega } from '../utils/producao';

const { data: itens, isLoading, isError } = useQuadroProducao(ref(true));
const { abrirOS, abrindo } = useAbrirOS();

// --- Filtros (D17) -------------------------------------------------------------------
const status = ref('');                                   // '' = todos
const soAtrasadas = ref(false);
const busca = ref('');

/** As opções de status: só os que aparecem no quadro, com o texto do segmento. */
const opcoesStatus = computed<Record<string, FilterOption>>(() => {
  const vistos: Record<string, FilterOption> = {};
  for (const item of itens.value ?? []) vistos[item.status] = { label: item.rotulo_status, class: '', color: 'bg-brand-primary' };
  return vistos;
});

/** O BaseFilter fala `null` para "Todos"; o filtro guarda ''. */
const statusSelecionado = computed<string | null>({
  get: () => status.value || null,
  set: (valor) => { status.value = valor ?? ''; },
});

/** A ordem é a da API (pela previsão); os filtros só tiram linhas. */
const visiveis = computed(() => {
  const termo = busca.value.trim().toLocaleLowerCase('pt-BR');
  return (itens.value ?? []).filter((item) =>
    (!status.value || item.status === status.value)
    && (!soAtrasadas.value || item.moveis_atrasados > 0)
    && (!termo || `${item.numero_os} ${item.cliente ?? ''} ${item.projeto ?? ''}`.toLocaleLowerCase('pt-BR').includes(termo)));
});

/** Os números do topo (a mesma lista do quadro, sem filtro). */
const indicadores = computed(() => {
  const lista = itens.value ?? [];
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const emSeteDias = lista.filter((item) => {
    if (!item.previsao) return false;
    const dias = (new Date(`${item.previsao}T00:00:00`).getTime() - hoje.getTime()) / 86_400_000;
    return dias >= 0 && dias <= 7;
  }).length;
  return {
    total: lista.length,
    atrasadas: lista.filter((item) => item.moveis_atrasados > 0).length,
    emSeteDias,
    prontos: lista.reduce((soma, item) => soma + item.progresso.moveis_prontos, 0),
    moveis: lista.reduce((soma, item) => soma + item.progresso.moveis_total, 0),
  };
});

/** Aguardando material pede atenção; aguardando entrega é produção pronta. */
const TOM_STATUS: Record<string, TomStatus> = { AGUARDANDO_PECAS: 'alerta', AGUARDANDO_RETIRADA: 'sucesso' };

const percentual = (item: ItemQuadro) =>
  (item.progresso.etapas_total ? Math.round((item.progresso.etapas_concluidas / item.progresso.etapas_total) * 100) : 0);

/** "05/11 (12 dias)" ou "03/10 (5 dias atrasada)". Produção concluída não atrasa. */
function entrega(item: ItemQuadro): { texto: string; atrasada: boolean } | null {
  if (!item.previsao) return null;
  const prazo = prazoDaEntrega(item.previsao);
  const atrasada = prazo.atrasada && !item.producao_concluida;
  const quando = prazo.atrasada ? prazo.texto : prazo.texto.replace(/^faltam? /, '');
  return { texto: `${diaMes(item.previsao)} (${quando})`, atrasada };
}
</script>

<template>
  <div class="space-y-6 md:space-y-8" data-testid="quadro-producao">
    <!-- Indicadores do quadro -->
    <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 md:gap-6 lg:grid-cols-4">
      <BaseStatsCard :icon="Hammer" label="OS no quadro" :value="String(indicadores.total)" />
      <BaseStatsCard
        :icon="AlertTriangle"
        label="Com atraso"
        :value="String(indicadores.atrasadas)"
        :tone="indicadores.atrasadas ? 'perigo' : 'neutro'"
      />
      <BaseStatsCard :icon="CalendarClock" label="Entregas em 7 dias" :value="String(indicadores.emSeteDias)" />
      <BaseStatsCard :icon="CheckCircle2" label="Móveis prontos" :value="`${indicadores.prontos} de ${indicadores.moveis}`" />
    </div>

    <BaseTableContainer
      :is-loading="isLoading"
      :is-error="isError"
      :is-empty="!visiveis.length"
      :total-items="visiveis.length"
      item-label="ordem de serviço"
      item-label-plural="ordens de serviço"
      error-title="Não foi possível carregar o quadro agora."
    >
      <!-- Filtros (D17) -->
      <template #toolbar>
        <div class="min-w-56 flex-1" data-testid="busca-quadro">
          <BaseSearchInput v-model="busca" placeholder="Cliente, projeto ou OS" />
        </div>
        <div data-testid="filtro-status">
          <BaseFilter v-model="statusSelecionado" :filter-config="opcoesStatus" title="Situação da OS" button-label="Situação" />
        </div>
        <div class="shrink-0" data-testid="so-atrasadas">
          <BaseCheckbox v-model="soAtrasadas" label="Só atrasadas" />
        </div>
      </template>

      <template #empty>
        <p class="py-12 text-center text-sm text-zinc-500" data-testid="quadro-vazio">Nenhuma OS em produção com esse filtro.</p>
      </template>

      <table class="w-full min-w-220 text-sm">
        <thead>
          <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
            <th class="px-5 py-3">OS</th>
            <th class="px-5 py-3">Cliente</th>
            <th class="px-5 py-3">Projeto</th>
            <th class="px-5 py-3">Situação</th>
            <th class="px-5 py-3">Progresso</th>
            <th class="px-5 py-3">Prontos</th>
            <th class="px-5 py-3">Próxima etapa</th>
            <th class="px-5 py-3">Entrega</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr v-for="item in visiveis" :key="item.numero_os" class="hover:bg-zinc-50/60" :data-testid="`linha-${item.numero_os}`">
            <td class="px-5 py-3 whitespace-nowrap">
              <!-- D16: abre a OS já na aba Produção -->
              <button
                type="button"
                class="font-semibold text-brand-primary hover:underline cursor-pointer disabled:opacity-60"
                :disabled="abrindo"
                :data-testid="`abrir-${item.numero_os}`"
                @click="abrirOS(item.numero_os, { abaInicial: 'producao' })"
              >
                {{ item.numero_os }}
              </button>
            </td>
            <td class="px-5 py-3 font-medium text-zinc-800">{{ item.cliente ?? '—' }}</td>
            <td class="px-5 py-3 text-zinc-600">{{ item.projeto ?? '—' }}</td>
            <td class="px-5 py-3"><BaseStatusPill :tom="TOM_STATUS[item.status] ?? 'info'">{{ item.rotulo_status }}</BaseStatusPill></td>
            <td class="px-5 py-3">
              <div class="flex items-center gap-2.5">
                <div class="w-28"><BaseProgressBar :valor="percentual(item)" :tom="percentual(item) >= 100 ? 'sucesso' : 'primario'" /></div>
                <span class="tabular-nums text-xs text-zinc-500">{{ percentual(item) }}%</span>
              </div>
            </td>
            <td class="px-5 py-3 tabular-nums text-zinc-700">{{ item.progresso.moveis_prontos }} de {{ item.progresso.moveis_total }}</td>
            <td class="px-5 py-3 text-zinc-700">
              <template v-if="item.proxima_etapa">{{ item.proxima_etapa.nome }} ({{ item.proxima_etapa.moveis }})</template>
              <template v-else>—</template>
            </td>
            <td class="px-5 py-3 whitespace-nowrap" data-testid="entrega">
              <span
                v-if="entrega(item)"
                class="inline-flex items-center gap-1 tabular-nums"
                :class="entrega(item)!.atrasada ? 'font-semibold text-red-700' : 'text-zinc-700'"
              >
                <AlertTriangle v-if="entrega(item)!.atrasada" :size="12" />
                {{ entrega(item)!.texto }}
              </span>
              <span v-else class="text-zinc-400">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </BaseTableContainer>
  </div>
</template>
