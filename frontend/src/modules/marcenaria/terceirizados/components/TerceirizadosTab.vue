<script setup lang="ts">
/**
 * @component TerceirizadosTab
 * @description Aba "Terceirizados" da tela de Serviços (Spec 11B D10-D12).
 *
 * Todos os móveis pedidos às centrais nas OS abertas, agrupados por central
 * (o dono resolve todos os móveis da mesma central numa ligação só). O
 * filtro já abre em "Pedido enviado": é o que se cobra. Só lê: as ações
 * ficam na OS, que abre com um clique no número.
 */
import { computed, ref } from 'vue';
import { AlertTriangle, Building2, Phone } from 'lucide-vue-next';

import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import type { FilterOption } from '@/shared/types/filter.types';

import { formatDataPura } from '@/shared/utils/date.utils';
import { formatTelefone } from '@/shared/utils/document.utils';
import { useAbrirOS } from '@/modules/marcenaria/orcamentos/composables/useAbrirOS';

import { useTerceirizadosEmAberto } from '../composables/useTerceirizadosEmAberto';
import { SITUACOES, type SituacaoTerceirizado } from '../schemas/terceirizado.schema';
import { diasDeAtraso, nomeDoPedido, ROTULO_SITUACAO, seloDaSituacao } from '../utils/terceirizados';

// --- Filtros (D11): padrão "Pedido enviado" -------------------------------------------
/** '' = todas as situações. */
const situacaoEscolhida = ref<SituacaoTerceirizado | ''>('ENVIADO');

/** O BaseFilter fala `null` para "Todos". */
const situacaoSelecionada = computed<string | null>({
  get: () => situacaoEscolhida.value || null,
  set: (valor) => { situacaoEscolhida.value = (valor ?? '') as SituacaoTerceirizado | ''; },
});
const CORES_SITUACAO: Record<SituacaoTerceirizado, string> = {
  A_PEDIR: 'bg-zinc-400', ENVIADO: 'bg-blue-500', RECEBIDO: 'bg-amber-500', CONFERIDO: 'bg-emerald-500',
};
const opcoesSituacao = Object.fromEntries(
  SITUACOES.map((s) => [s, { label: ROTULO_SITUACAO[s], class: '', color: CORES_SITUACAO[s] }]),
) as Record<string, FilterOption>;
const soAtrasados = ref(false);
const situacao = computed(() => situacaoEscolhida.value || null);

const { grupos, isLoading, isError } = useTerceirizadosEmAberto(situacao, soAtrasados);
const { abrirOS, abrindo } = useAbrirOS();

/** D12: "Madeiranit · (85) 3333-0000 · 3 pedidos, 1 atrasado". */
function resumoDoGrupo(pedidos: number, atrasados: number): string {
  const partes = [`${pedidos} ${pedidos === 1 ? 'pedido' : 'pedidos'}`];
  if (atrasados) partes.push(`${atrasados} ${atrasados === 1 ? 'atrasado' : 'atrasados'}`);
  return partes.join(', ');
}
</script>

<template>
  <div class="space-y-6" data-testid="aba-terceirizados">
    <!-- Filtros -->
    <div class="flex flex-wrap items-center gap-4 rounded-2xl border border-zinc-200 bg-white px-6 py-4">
      <div data-testid="filtro-situacao">
        <BaseFilter v-model="situacaoSelecionada" :filter-config="opcoesSituacao" title="Situação do pedido" button-label="Situação" />
      </div>
      <div class="shrink-0" data-testid="filtro-atrasados">
        <BaseCheckbox v-model="soAtrasados" label="Só atrasados" />
      </div>
      <p class="ml-auto text-xs text-zinc-500">Móveis pedidos às centrais parceiras, agrupados por central.</p>
    </div>

    <p v-if="isLoading" class="text-sm text-zinc-500">Carregando…</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar os terceirizados agora.</p>
    <div
      v-else-if="!grupos.length"
      class="flex flex-col items-center gap-2 rounded-2xl border border-zinc-200 bg-white px-6 py-12 text-center"
      data-testid="sem-terceirizados"
    >
      <span class="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-zinc-400"><Building2 :size="22" /></span>
      <p class="text-sm font-medium text-zinc-600">Nenhum móvel de central com esse filtro.</p>
    </div>

    <!-- Um bloco por central (D11, D12) -->
    <template v-else>
      <section
        v-for="grupo in grupos"
        :key="grupo.chave"
        class="overflow-hidden rounded-2xl border border-zinc-200 bg-white"
        :data-testid="`grupo-${grupo.chave}`"
      >
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 px-6 py-4">
          <div class="flex items-center gap-3">
            <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-primary-light text-brand-primary" aria-hidden="true">
              <Building2 :size="18" />
            </span>
            <div>
              <strong class="text-base font-semibold text-zinc-900">{{ grupo.nome }}</strong>
              <p v-if="grupo.telefone" class="flex items-center gap-1 text-xs text-zinc-500">
                <Phone :size="12" /> {{ formatTelefone(grupo.telefone) }}
              </p>
            </div>
          </div>
          <span data-testid="resumo-grupo">
            <BaseStatusPill :tom="grupo.atrasados ? 'perigo' : 'info'">{{ resumoDoGrupo(grupo.pedidos, grupo.atrasados) }}</BaseStatusPill>
          </span>
        </header>

        <div class="overflow-x-auto">
          <table class="w-full min-w-200 text-left text-sm">
            <thead>
              <tr class="border-b border-zinc-100 bg-zinc-50 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                <th class="px-5 py-3">OS</th>
                <th class="px-5 py-3">Cliente</th>
                <th class="px-5 py-3">Móvel</th>
                <th class="px-5 py-3">Pedido</th>
                <th class="px-5 py-3">Enviado em</th>
                <th class="px-5 py-3">Previsão</th>
                <th class="px-5 py-3">Atraso</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-100">
              <tr
                v-for="item in grupo.itens"
                :key="`${item.numero_os}-${item.movel_id}`"
                class="hover:bg-zinc-50/60"
                :data-testid="`item-${item.movel_id}`"
              >
                <td class="px-5 py-3 whitespace-nowrap">
                  <!-- O número abre a OS (o mesmo caminho do sino de notificações) -->
                  <button
                    type="button"
                    class="font-semibold text-brand-primary hover:underline cursor-pointer disabled:opacity-60"
                    :disabled="abrindo"
                    :data-testid="`abrir-os-${item.movel_id}`"
                    @click="abrirOS(item.numero_os)"
                  >
                    {{ item.numero_os }}
                  </button>
                </td>
                <td class="px-5 py-3 font-medium text-zinc-800">{{ item.cliente ?? '—' }}</td>
                <td class="px-5 py-3">
                  <p class="font-medium text-zinc-900">{{ item.nome }}</p>
                  <p class="text-xs text-zinc-500">{{ item.ambiente }} · {{ item.quantidade }}×</p>
                </td>
                <td class="px-5 py-3">
                  <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap" :class="seloDaSituacao(item).classe">{{ seloDaSituacao(item).texto }}</span>
                  <p v-if="item.pedido" class="mt-0.5 text-xs text-zinc-600">{{ nomeDoPedido(item) }}</p>
                </td>
                <td class="px-5 py-3 tabular-nums text-zinc-700">{{ formatDataPura(item.enviado_em, '—') }}</td>
                <td class="px-5 py-3 tabular-nums text-zinc-700">{{ formatDataPura(item.previsao, '—') }}</td>
                <td class="px-5 py-3">
                  <span v-if="diasDeAtraso(item)" class="inline-flex items-center gap-1 text-xs font-semibold text-red-700" data-testid="atraso">
                    <AlertTriangle :size="12" />
                    {{ diasDeAtraso(item) }} {{ diasDeAtraso(item) === 1 ? 'dia' : 'dias' }}
                  </span>
                  <span v-else class="text-zinc-400">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
