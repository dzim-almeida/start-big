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
import { AlertTriangle } from 'lucide-vue-next';

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
const opcoesStatus = computed(() => {
  const vistos = new Map<string, string>();
  for (const item of itens.value ?? []) vistos.set(item.status, item.rotulo_status);
  return [...vistos.entries()].map(([valor, rotulo]) => ({ valor, rotulo }));
});

/** A ordem é a da API (pela previsão); os filtros só tiram linhas. */
const visiveis = computed(() => {
  const termo = busca.value.trim().toLocaleLowerCase('pt-BR');
  return (itens.value ?? []).filter((item) =>
    (!status.value || item.status === status.value)
    && (!soAtrasadas.value || item.moveis_atrasados > 0)
    && (!termo || `${item.numero_os} ${item.cliente ?? ''} ${item.projeto ?? ''}`.toLocaleLowerCase('pt-BR').includes(termo)));
});

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
  <div class="space-y-4" data-testid="quadro-producao">
    <!-- Filtros -->
    <div class="flex flex-wrap items-end gap-4">
      <label class="flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Status
        <select
          v-model="status"
          class="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="filtro-status"
        >
          <option value="">Todos</option>
          <option v-for="opcao in opcoesStatus" :key="opcao.valor" :value="opcao.valor">{{ opcao.rotulo }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Buscar
        <input
          v-model="busca"
          type="search"
          placeholder="Cliente, projeto ou OS"
          class="w-64 rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="busca-quadro"
        />
      </label>
      <label class="flex items-center gap-2 pb-2 text-sm text-zinc-700">
        <input v-model="soAtrasadas" type="checkbox" class="accent-brand-primary" data-testid="so-atrasadas" />
        Só atrasadas
      </label>
    </div>

    <p v-if="isLoading" class="text-sm text-zinc-400">Carregando…</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar o quadro agora.</p>
    <p v-else-if="!visiveis.length" class="rounded-xl border border-zinc-200 bg-white px-4 py-6 text-center text-sm text-zinc-500" data-testid="quadro-vazio">
      Nenhuma OS em produção com esse filtro.
    </p>

    <div v-else class="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
      <table class="w-full text-left text-sm">
        <thead class="bg-zinc-50 text-xs text-zinc-500">
          <tr>
            <th class="px-4 py-2 font-medium">OS</th>
            <th class="px-4 py-2 font-medium">Cliente</th>
            <th class="px-4 py-2 font-medium">Projeto</th>
            <th class="px-4 py-2 font-medium">Status</th>
            <th class="px-4 py-2 font-medium">Progresso</th>
            <th class="px-4 py-2 font-medium">Prontos</th>
            <th class="px-4 py-2 font-medium">Próxima</th>
            <th class="px-4 py-2 font-medium">Entrega</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in visiveis" :key="item.numero_os" class="border-t border-zinc-100" :data-testid="`linha-${item.numero_os}`">
            <td class="px-4 py-2">
              <!-- D16: abre a OS já na aba Produção -->
              <button
                type="button"
                class="font-medium text-brand-primary hover:underline cursor-pointer disabled:opacity-60"
                :disabled="abrindo"
                :data-testid="`abrir-${item.numero_os}`"
                @click="abrirOS(item.numero_os, { abaInicial: 'producao' })"
              >
                {{ item.numero_os }}
              </button>
            </td>
            <td class="px-4 py-2 text-zinc-700">{{ item.cliente ?? '—' }}</td>
            <td class="px-4 py-2 text-zinc-700">{{ item.projeto ?? '—' }}</td>
            <td class="px-4 py-2 text-zinc-700">{{ item.rotulo_status }}</td>
            <td class="px-4 py-2">
              <div class="flex items-center gap-2">
                <div class="h-2 w-24 overflow-hidden rounded-full bg-zinc-100" aria-hidden="true">
                  <div class="h-full bg-emerald-500" :style="{ width: `${percentual(item)}%` }" />
                </div>
                <span class="tabular-nums text-xs text-zinc-600">{{ percentual(item) }}%</span>
              </div>
            </td>
            <td class="px-4 py-2 tabular-nums text-zinc-700">{{ item.progresso.moveis_prontos }} de {{ item.progresso.moveis_total }}</td>
            <td class="px-4 py-2 text-zinc-700">
              <template v-if="item.proxima_etapa">{{ item.proxima_etapa.nome }} ({{ item.proxima_etapa.moveis }})</template>
              <template v-else>—</template>
            </td>
            <td class="px-4 py-2" data-testid="entrega">
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
    </div>
  </div>
</template>
