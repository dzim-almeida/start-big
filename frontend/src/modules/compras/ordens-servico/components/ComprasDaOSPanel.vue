<script setup lang="ts">
/**
 * "Compras desta OS" (módulo Compras, fase 6) — na aba Serviços e Peças.
 *
 * Para cada peça APROVADA da OS: quanto o estoque cobre (em fila: a OS mais
 * antiga pega primeiro), quanto está em pedido ligado a ela e quanto ainda
 * falta comprar. Avisa quando o pedido chega depois da previsão da OS (RC08).
 *
 * Lê o que está SALVO: item acrescentado agora só entra depois de salvar a OS.
 * Quem renderiza (OSFormTabsContent) já conferiu módulo e permissão; o
 * componente nem é baixado por quem não tem Compras.
 */
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { AlertTriangle, PackageCheck, ShoppingCart, Truck } from 'lucide-vue-next';

import { formatDataPura } from '@/shared/utils/date.utils';

import { useComprasDaOSQuery } from '../../shared/composables/useCompras';
import { SITUACOES_PEDIDO } from '../../shared/constants/situacoes';
import type { CompraDaOSItem } from '../../shared/types/compras.types';

const props = defineProps<{ osId: number }>();

const router = useRouter();
const idRef = computed(() => props.osId);
const { data, isLoading, isError } = useComprasDaOSQuery(idRef);

const SITUACAO: Record<CompraDaOSItem['situacao'], { rotulo: string; classe: string }> = {
  NO_ESTOQUE: { rotulo: 'No estoque', classe: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  EM_PEDIDO: { rotulo: 'Em pedido', classe: 'bg-blue-50 text-blue-700 border border-blue-200' },
  FALTA: { rotulo: 'Falta comprar', classe: 'bg-rose-50 text-rose-700 border border-rose-200' },
};

const algoFalta = computed(() => (data.value?.itens ?? []).some((i) => i.situacao === 'FALTA'));

function qtd(n: number): string {
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}

function irParaNecessidades() {
  router.push({ name: 'purchases-needs' });
}
</script>

<template>
  <section class="mt-6 rounded-xl border border-slate-200 bg-white p-4 space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <div class="bg-brand-primary-light p-2 rounded-lg text-brand-primary">
          <Truck :size="18" />
        </div>
        <div>
          <h5 class="text-sm font-bold text-slate-700">Compras desta OS</h5>
          <p class="text-xs text-slate-500">Peças aprovadas: o que o estoque cobre, o que está pedido e o que falta.</p>
        </div>
      </div>
      <button
        v-if="algoFalta"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-lg bg-brand-primary px-3 py-1.5 text-xs font-bold text-white hover:opacity-90 cursor-pointer"
        @click="irParaNecessidades"
      >
        <ShoppingCart :size="14" /> Comprar nas Necessidades
      </button>
    </div>

    <p
      v-if="data?.aberta && data.compra_bloqueada"
      class="mb-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2"
    >
      Aguardando o sinal: o material está reservado, mas só entra nas Necessidades quando o sinal for pago
      ou o gestor liberar a compra no trilho da OS.
    </p>
    <p v-if="isLoading" class="py-4 text-center text-xs text-slate-400">Conferindo o estoque…</p>
    <p v-else-if="isError" class="text-xs text-rose-600">Não foi possível conferir as compras desta OS.</p>
    <p v-else-if="data && !data.aberta" class="text-xs text-slate-500">
      OS fechada: as peças já saíram do estoque (ou não vão sair).
    </p>
    <p v-else-if="!data?.itens.length" class="flex items-center gap-2 text-xs text-slate-500">
      <PackageCheck :size="14" class="text-slate-400" />
      Nenhuma peça do estoque aprovada nesta OS (as recém-acrescentadas aparecem depois de salvar).
    </p>

    <ul v-else class="space-y-2">
      <li v-for="item in data.itens" :key="item.produto_id" class="rounded-lg border border-slate-100 p-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0">
            <p class="text-sm font-semibold text-slate-700">{{ item.descricao }}</p>
            <p class="text-xs text-slate-500">
              Precisa {{ qtd(item.necessario) }} {{ item.unidade }}
              · estoque cobre {{ qtd(item.no_estoque) }}
              <template v-if="item.em_pedido"> · em pedido {{ qtd(item.em_pedido) }}</template>
              <template v-if="item.falta">
                · <strong class="text-rose-700">faltam {{ qtd(item.falta) }}</strong>
              </template>
            </p>
          </div>
          <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="SITUACAO[item.situacao].classe">
            {{ SITUACAO[item.situacao].rotulo }}
          </span>
        </div>

        <ul v-if="item.pedidos.length" class="mt-2 space-y-1 border-t border-slate-100 pt-2">
          <li v-for="p in item.pedidos" :key="p.pedido_id" class="flex flex-wrap items-center gap-2 text-xs text-slate-600">
            <span class="font-semibold text-slate-700">{{ p.codigo }}</span>
            <span class="rounded-full px-1.5 py-0.5 text-[10px] font-semibold" :class="SITUACOES_PEDIDO[p.situacao].class">
              {{ SITUACOES_PEDIDO[p.situacao].label }}
            </span>
            <span>{{ qtd(p.quantidade) }} {{ item.unidade }}</span>
            <span v-if="p.previsao_entrega">· chega até {{ formatDataPura(p.previsao_entrega) }}</span>
            <span v-if="p.atrasa_os" class="inline-flex items-center gap-1 font-semibold text-amber-700">
              <AlertTriangle :size="12" /> depois da previsão da OS
            </span>
          </li>
        </ul>
      </li>
    </ul>
  </section>
</template>
