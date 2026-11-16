<script setup lang="ts">
/**
 * Pedidos de compra — o que foi pedido, a quem, e quando chega.
 *
 * Mesmo desenho das Contas a Pagar: PageReview com a ação principal, e a busca
 * e o filtro DENTRO da tabela (são ferramentas da listagem, não da página).
 * O clique na linha abre o DETALHE, onde moram as ações de cada situação.
 *
 * Chegando das Necessidades (`?situacao=RASCUNHO`), a lista já vem filtrada nos
 * rascunhos que acabaram de nascer.
 */
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { AlertTriangle, Plus } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { formatData, formatDataPura } from '@/shared/utils/date.utils';

import SituacaoPedidoBadge from '../../shared/components/SituacaoPedidoBadge.vue';
import { useAcessoCompras } from '../../shared/composables/useAcessoCompras';
import { usePedidosQuery } from '../../shared/composables/useCompras';
import { SITUACOES_PEDIDO } from '../../shared/constants/situacoes';
import type { PedidoRead, SituacaoPedido } from '../../shared/types/compras.types';
import PedidoDetalheModal from '../components/PedidoDetalheModal.vue';
import PedidoFormModal from '../components/PedidoFormModal.vue';

const route = useRoute();
const { podeGerenciar, podeVerCusto } = useAcessoCompras();

const POR_PAGINA = 20;
const pagina = ref(1);
const busca = ref('');
const situacao = ref<string | null>(
  typeof route.query.situacao === 'string' && route.query.situacao in SITUACOES_PEDIDO ? route.query.situacao : null,
);

/** Recorte "só os atrasados" — vem do aviso logo abaixo do título. */
const soAtrasados = ref(route.query.atrasados === '1');

const filtros = computed(() => ({
  limit: POR_PAGINA,
  offset: (pagina.value - 1) * POR_PAGINA,
  situacao: (situacao.value || undefined) as SituacaoPedido | undefined,
  busca: busca.value.trim() || undefined,
  atrasados: soAtrasados.value || undefined,
}));

// Filtrar volta para a primeira página: na página 4 de um filtro novo, a lista
// pareceria vazia — há resultado, mas não na altura em que se parou.
watch([situacao, busca, soAtrasados], () => { pagina.value = 1; });

const { data: listagem, isLoading, isError } = usePedidosQuery(filtros);

/**
 * Quantos estão atrasados (enviados com a previsão já passada). Consulta
 * própria e mínima (limit 1): só o total importa para o aviso.
 */
const { data: atrasados } = usePedidosQuery({ atrasados: true, limit: 1, offset: 0 });
const totalAtrasados = computed(() => atrasados.value?.total_itens ?? 0);
const totalPaginas = computed(() => Math.max(1, Math.ceil((listagem.value?.total_itens ?? 0) / POR_PAGINA)));

const detalheId = ref<number | null>(null);
const formAberto = ref(false);
const emEdicao = ref<PedidoRead | null>(null);

function novoPedido() {
  emEdicao.value = null;
  formAberto.value = true;
}

function editar(pedido: PedidoRead) {
  detalheId.value = null;
  emEdicao.value = pedido;
  formAberto.value = true;
}

function aoSalvar(pedido: PedidoRead) {
  detalheId.value = pedido.id;
}
</script>

<template>
  <div class="flex flex-col gap-6 md:gap-8">
    <div class="flex items-center justify-between gap-4">
      <PageReview title="Pedidos de Compra" description="O que foi pedido, a quem, e quando chega" />
      <BaseButton v-if="podeGerenciar" variant="primary" @click="novoPedido">
        <Plus :size="16" class="mr-1.5" /> Novo pedido
      </BaseButton>
    </div>

    <!-- Pedido atrasado é o que o dono precisa cobrar do fornecedor hoje. -->
    <div
      v-if="totalAtrasados && !soAtrasados"
      class="flex flex-wrap items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-800"
    >
      <AlertTriangle :size="15" />
      <span>
        <strong>{{ totalAtrasados }}</strong>
        {{ totalAtrasados === 1 ? 'pedido passou' : 'pedidos passaram' }} da data de entrega e não chegaram.
      </span>
      <button type="button" class="font-semibold underline underline-offset-2 cursor-pointer" @click="soAtrasados = true">
        Ver {{ totalAtrasados === 1 ? 'qual' : 'quais' }}
      </button>
    </div>
    <div
      v-else-if="soAtrasados"
      class="flex flex-wrap items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-800"
    >
      <span>Mostrando <strong>só os atrasados</strong>.</span>
      <button type="button" class="font-semibold underline underline-offset-2 cursor-pointer" @click="soAtrasados = false">
        Mostrar todos
      </button>
    </div>

    <BaseTableContainer
      :is-loading="isLoading"
      :is-error="isError"
      :is-empty="!listagem?.itens.length"
      :current-page="pagina"
      :total-pages="totalPaginas"
      :total-items="listagem?.total_itens ?? 0"
      item-label="pedido"
      item-label-plural="pedidos"
      empty-title="Nenhum pedido de compra"
      empty-description="Gere pelas Necessidades (o que está abaixo do mínimo) ou crie um pedido avulso."
      @update:current-page="pagina = $event"
    >
      <template #toolbar>
        <BaseSearchInput v-model="busca" placeholder="Número (PC-12) ou fornecedor" />
        <BaseFilter v-model="situacao" :filterConfig="SITUACOES_PEDIDO" />
      </template>

      <table class="w-full min-w-180 text-sm">
        <thead>
          <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
            <th class="px-5 py-3">Pedido</th>
            <th class="px-5 py-3">Fornecedor</th>
            <th class="px-5 py-3">Entrega até</th>
            <th class="px-5 py-3 text-right">Itens</th>
            <th v-if="podeVerCusto" class="px-5 py-3 text-right">Total</th>
            <th class="px-5 py-3">Situação</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="p in listagem?.itens ?? []"
            :key="p.id"
            class="cursor-pointer hover:bg-zinc-50/60"
            @click="detalheId = p.id"
          >
            <td class="px-5 py-3">
              <p class="font-semibold text-zinc-800">{{ p.codigo }}</p>
              <p class="text-[11px] text-zinc-400">{{ formatData(p.criado_em) }}</p>
            </td>
            <td class="px-5 py-3 text-zinc-700">{{ p.fornecedor_nome }}</td>
            <td class="px-5 py-3" :class="p.atrasado ? 'font-semibold text-rose-600' : 'text-zinc-600'">
              {{ formatDataPura(p.previsao_entrega, '—') }}
            </td>
            <td class="px-5 py-3 text-right tabular-nums text-zinc-600">{{ p.quantidade_itens }}</td>
            <td v-if="podeVerCusto" class="px-5 py-3 text-right font-semibold tabular-nums text-zinc-800">
              {{ formatCurrency(p.valor_total ?? 0) }}
            </td>
            <td class="px-5 py-3">
              <SituacaoPedidoBadge :situacao="p.situacao" :atrasado="p.atrasado" />
            </td>
          </tr>
        </tbody>
      </table>
    </BaseTableContainer>

    <PedidoDetalheModal :pedido-id="detalheId" @fechar="detalheId = null" @editar="editar" />
    <PedidoFormModal :aberto="formAberto" :pedido="emEdicao" @fechar="formAberto = false" @salvo="aoSalvar" />
  </div>
</template>
