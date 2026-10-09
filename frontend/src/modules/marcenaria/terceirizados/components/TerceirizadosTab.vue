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
import { AlertTriangle } from 'lucide-vue-next';

import { formatDataPura } from '@/shared/utils/date.utils';
import { formatTelefone } from '@/shared/utils/document.utils';
import { useAbrirOS } from '@/modules/marcenaria/orcamentos/composables/useAbrirOS';

import { useTerceirizadosEmAberto } from '../composables/useTerceirizadosEmAberto';
import { SITUACOES, type SituacaoTerceirizado } from '../schemas/terceirizado.schema';
import { diasDeAtraso, nomeDoPedido, ROTULO_SITUACAO, seloDaSituacao } from '../utils/terceirizados';

// --- Filtros (D11): padrão "Pedido enviado" -------------------------------------------
/** '' = todas as situações (o <select> nativo não guarda null). */
const situacaoEscolhida = ref<SituacaoTerceirizado | ''>('ENVIADO');
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
  <div class="space-y-4" data-testid="aba-terceirizados">
    <!-- Filtros -->
    <div class="flex flex-wrap items-end gap-4">
      <label class="flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Situação
        <select
          v-model="situacaoEscolhida"
          class="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="filtro-situacao"
        >
          <option value="">Todas</option>
          <option v-for="s in SITUACOES" :key="s" :value="s">{{ ROTULO_SITUACAO[s] }}</option>
        </select>
      </label>
      <label class="flex items-center gap-2 pb-2 text-sm text-zinc-700">
        <input v-model="soAtrasados" type="checkbox" class="accent-brand-primary" data-testid="filtro-atrasados" />
        Só atrasados
      </label>
    </div>

    <p v-if="isLoading" class="text-sm text-zinc-400">Carregando…</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar os terceirizados agora.</p>
    <p v-else-if="!grupos.length" class="rounded-xl border border-zinc-200 bg-white px-4 py-6 text-center text-sm text-zinc-500" data-testid="sem-terceirizados">
      Nenhum móvel de central com esse filtro.
    </p>

    <!-- Um bloco por central (D11, D12) -->
    <template v-else>
      <section
        v-for="grupo in grupos"
        :key="grupo.chave"
        class="overflow-hidden rounded-xl border border-zinc-200 bg-white"
        :data-testid="`grupo-${grupo.chave}`"
      >
        <header class="flex flex-wrap items-center gap-x-2 border-b border-zinc-100 bg-zinc-50 px-4 py-2 text-sm">
          <strong class="text-zinc-800">{{ grupo.nome }}</strong>
          <span v-if="grupo.telefone" class="text-zinc-500">· {{ formatTelefone(grupo.telefone) }}</span>
          <span class="text-zinc-500" :class="{ 'font-semibold text-red-700': grupo.atrasados }" data-testid="resumo-grupo">
            · {{ resumoDoGrupo(grupo.pedidos, grupo.atrasados) }}
          </span>
        </header>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs text-zinc-500">
              <tr>
                <th class="px-4 py-2 font-medium">OS</th>
                <th class="px-4 py-2 font-medium">Cliente</th>
                <th class="px-4 py-2 font-medium">Móvel</th>
                <th class="px-4 py-2 font-medium">Pedido</th>
                <th class="px-4 py-2 font-medium">Enviado em</th>
                <th class="px-4 py-2 font-medium">Previsão</th>
                <th class="px-4 py-2 font-medium">Atraso</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in grupo.itens"
                :key="`${item.numero_os}-${item.movel_id}`"
                class="border-t border-zinc-100"
                :data-testid="`item-${item.movel_id}`"
              >
                <td class="px-4 py-2">
                  <!-- O número abre a OS (o mesmo caminho do sino de notificações) -->
                  <button
                    type="button"
                    class="font-medium text-brand-primary hover:underline cursor-pointer disabled:opacity-60"
                    :disabled="abrindo"
                    :data-testid="`abrir-os-${item.movel_id}`"
                    @click="abrirOS(item.numero_os)"
                  >
                    {{ item.numero_os }}
                  </button>
                </td>
                <td class="px-4 py-2 text-zinc-700">{{ item.cliente ?? '—' }}</td>
                <td class="px-4 py-2">
                  <p class="font-medium text-zinc-900">{{ item.nome }}</p>
                  <p class="text-xs text-zinc-500">{{ item.ambiente }} · {{ item.quantidade }}×</p>
                </td>
                <td class="px-4 py-2">
                  <span class="rounded-full border px-2 py-0.5 text-[11px]" :class="seloDaSituacao(item).classe">{{ seloDaSituacao(item).texto }}</span>
                  <p v-if="item.pedido" class="mt-0.5 text-xs text-zinc-600">{{ nomeDoPedido(item) }}</p>
                </td>
                <td class="px-4 py-2 tabular-nums text-zinc-700">{{ formatDataPura(item.enviado_em, '—') }}</td>
                <td class="px-4 py-2 tabular-nums text-zinc-700">{{ formatDataPura(item.previsao, '—') }}</td>
                <td class="px-4 py-2">
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
