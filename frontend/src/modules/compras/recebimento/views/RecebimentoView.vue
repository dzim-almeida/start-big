<script setup lang="ts">
/**
 * Recebimento — confira o que chegou e dê entrada no estoque (fase 3).
 *
 * À esquerda, o que está a receber (enviados e recebidos em parte); à direita,
 * a conferência do escolhido. Em tela estreita uma coisa de cada vez: escolher
 * o pedido abre a conferência, e "Voltar" retorna à lista.
 *
 * Chegando do detalhe do pedido (`?pedido=ID`), já abre na conferência dele.
 */
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, PackageOpen, Truck } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import { formatDataPura } from '@/shared/utils/date.utils';

import SituacaoPedidoBadge from '../../shared/components/SituacaoPedidoBadge.vue';
import { usePedidoQuery, usePedidosQuery } from '../../shared/composables/useCompras';
import type { PedidoRead } from '../../shared/types/compras.types';
import ConferenciaRecebimento from '../components/ConferenciaRecebimento.vue';

const route = useRoute();
const router = useRouter();

const busca = ref('');
const filtros = computed(() => ({
  a_receber: true,
  busca: busca.value.trim() || undefined,
  limit: 50,
  offset: 0,
}));
const { data: listagem, isLoading } = usePedidosQuery(filtros);

const selecionado = ref<number | null>(Number(route.query.pedido) || null);
const { data: pedido, isLoading: carregandoPedido } = usePedidoQuery(selecionado);

watch(selecionado, (id) => {
  router.replace({ query: id ? { pedido: String(id) } : {} });
});

function aoConcluir(atualizado: PedidoRead) {
  // Recebeu tudo (ou encerrou): sai da lista; parcial: continua na conferência.
  if (atualizado.situacao === 'RECEBIDO') selecionado.value = null;
}
</script>

<template>
  <div class="flex flex-col gap-6 md:gap-8">
    <PageReview title="Recebimento" description="Confira o que chegou e dê entrada no estoque" />

    <div class="grid gap-6 lg:grid-cols-[22rem_1fr]">
      <!-- Lista: some em tela estreita quando há um pedido aberto. -->
      <aside class="flex flex-col gap-3" :class="selecionado ? 'hidden lg:flex' : 'flex'">
        <BaseSearchInput v-model="busca" placeholder="Número ou fornecedor" />
        <p v-if="isLoading" class="py-6 text-center text-sm text-zinc-400">Carregando…</p>
        <div
          v-else-if="!listagem?.itens.length"
          class="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center"
        >
          <Truck :size="24" class="text-zinc-400" />
          <p class="text-sm font-medium text-zinc-700">Nada a receber</p>
          <p class="text-xs text-zinc-500">Os pedidos marcados como enviados aparecem aqui até chegarem.</p>
        </div>
        <button
          v-for="p in listagem?.itens ?? []"
          :key="p.id"
          type="button"
          class="flex flex-col gap-1.5 rounded-xl border bg-white p-4 text-left transition-colors cursor-pointer"
          :class="selecionado === p.id ? 'border-brand-primary ring-1 ring-brand-primary' : 'border-zinc-200 hover:border-zinc-300'"
          @click="selecionado = p.id"
        >
          <span class="flex items-center justify-between gap-2">
            <span class="font-semibold text-zinc-800">{{ p.codigo }}</span>
            <SituacaoPedidoBadge :situacao="p.situacao" :atrasado="p.atrasado" />
          </span>
          <span class="text-sm text-zinc-700">{{ p.fornecedor_nome }}</span>
          <span class="text-xs text-zinc-500">
            {{ p.quantidade_itens }} {{ p.quantidade_itens === 1 ? 'item' : 'itens' }} · entrega
            {{ formatDataPura(p.previsao_entrega, 'a combinar') }}
          </span>
        </button>
      </aside>

      <section class="rounded-2xl border border-zinc-200 bg-white p-4 md:p-6" :class="selecionado ? 'block' : 'hidden lg:block'">
        <button
          v-if="selecionado"
          type="button"
          class="mb-4 flex items-center gap-1.5 text-sm font-medium text-zinc-600 lg:hidden cursor-pointer"
          @click="selecionado = null"
        >
          <ArrowLeft :size="16" /> Voltar à lista
        </button>
        <p v-if="selecionado && carregandoPedido" class="py-10 text-center text-sm text-zinc-400">Carregando o pedido…</p>
        <ConferenciaRecebimento
          v-else-if="pedido && selecionado && (pedido.situacao === 'ENVIADO' || pedido.situacao === 'PARCIAL')"
          :pedido="pedido"
          @concluido="aoConcluir"
        />
        <div v-else-if="pedido && selecionado" class="py-10 text-center text-sm text-zinc-500">
          O pedido {{ pedido.codigo }} está {{ pedido.situacao.toLowerCase() }} e não tem o que receber.
        </div>
        <div v-else class="flex flex-col items-center gap-2 py-16 text-center">
          <PackageOpen :size="28" class="text-zinc-300" />
          <p class="text-sm text-zinc-500">Escolha um pedido para conferir a mercadoria.</p>
        </div>
      </section>
    </div>
  </div>
</template>
