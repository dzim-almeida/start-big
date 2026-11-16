<script setup lang="ts">
/**
 * Conferência da mercadoria que chegou, item a item (módulo Compras, fase 3).
 *
 * O LEITOR é o caminho principal: cada bipe soma 1 na linha. Bipar o código da
 * EMBALAGEM (o DUN do fardo) soma 1 fardo. Bipar o código da UNIDADE num item
 * comprado em fardo não soma nada — avisa: "este item é recebido em FD com 12;
 * bipe o fardo ou digite". Somar 1/12 de fardo não existe (quantidade inteira,
 * D3), e somar 1 fardo por uma lata bipada daria entrada em 11 que não vieram.
 *
 * Em CARTÕES, não em tabela: a mesma tela serve ao balcão e ao celular na
 * porta do depósito (D17).
 *
 * Quem só RECEBE (o almoxarife) não vê preço nem decide contas: o custo é o
 * do pedido e as contas seguem a regra (D8, D14).
 */
import { computed, ref, watch } from 'vue';
import { Minus, Plus, ScanBarcode, AlertTriangle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useToast } from '@/shared/composables/useToast';
import { formatCurrency } from '@/shared/utils/finance';
import { formatDataPura } from '@/shared/utils/date.utils';

import SituacaoPedidoBadge from '../../shared/components/SituacaoPedidoBadge.vue';
import { useAcessoCompras } from '../../shared/composables/useAcessoCompras';
import { useReceberPedido } from '../../shared/composables/useCompras';
import type { PedidoItemRead, PedidoRead } from '../../shared/types/compras.types';

const props = defineProps<{ pedido: PedidoRead }>();
const emit = defineEmits<{ concluido: [pedido: PedidoRead] }>();

const toast = useToast();
const { podeReceber, podeVerCusto } = useAcessoCompras();
const receber = useReceberPedido();

interface Conferencia {
  chegou: number;
  /** Reais por unidade de compra; só para quem vê custo. */
  custoReais: number | undefined;
}

const conferencia = ref<Record<number, Conferencia>>({});
const numeroNota = ref('');
const observacao = ref('');
const encerrarSaldo = ref(false);
const lancarContas = ref(true);
const codigo = ref('');

const pendentes = computed(() => props.pedido.itens.filter((i) => i.pendente > 0));

// Repovoa ao trocar de pedido (ou quando ele volta do servidor após uma entrada).
watch(
  () => props.pedido,
  (p) => {
    const nova: Record<number, Conferencia> = {};
    for (const item of p.itens) {
      nova[item.id] = {
        chegou: 0,
        custoReais: item.custo_unitario != null ? item.custo_unitario / 100 : undefined,
      };
    }
    conferencia.value = nova;
    numeroNota.value = '';
    observacao.value = '';
    encerrarSaldo.value = false;
    lancarContas.value = true;
  },
  { immediate: true },
);

function ajustar(item: PedidoItemRead, delta: number) {
  const c = conferencia.value[item.id];
  if (!c) return;
  const novo = Math.min(Math.max((Number(c.chegou) || 0) + delta, 0), item.pendente);
  if ((Number(c.chegou) || 0) + delta > item.pendente) {
    toast.error(`'${item.descricao}' já está completo`, `Faltavam ${item.pendente} ${item.unidade_compra}.`);
  }
  c.chegou = novo;
}

/** Leitor: Enter no campo de código. */
function bipar() {
  const lido = codigo.value.trim();
  codigo.value = '';
  if (!lido) return;

  // 1º: o código "principal" do item (o da embalagem, se compra em embalagem).
  const principal = pendentes.value.find((i) => i.codigos_barras[0] === lido);
  if (principal) {
    if (principal.fator > 1 && principal.embalagem_id == null) {
      // Item em "caixa com 6" sem embalagem cadastrada: o código é da unidade.
      avisarUnidade(principal);
      return;
    }
    ajustar(principal, 1);
    return;
  }
  // 2º: um código da UNIDADE num item comprado em embalagem.
  const daUnidade = pendentes.value.find((i) => i.codigos_barras.includes(lido));
  if (daUnidade) {
    if (daUnidade.fator > 1) {
      avisarUnidade(daUnidade);
      return;
    }
    ajustar(daUnidade, 1);
    return;
  }
  const jaCompleto = props.pedido.itens.find((i) => i.codigos_barras.includes(lido));
  toast.error(
    jaCompleto ? `'${jaCompleto.descricao}' já chegou todo` : 'Código não está neste pedido',
    jaCompleto ? 'Nada falta deste item.' : lido,
  );
}

function avisarUnidade(item: PedidoItemRead) {
  toast.error(
    `Bipou a unidade de '${item.descricao}'`,
    `Este item é recebido em ${item.unidade_compra} com ${item.fator}. Bipe o código do ${item.unidade_compra} ou digite a quantidade.`,
  );
}

const resumo = computed(() => {
  let itens = 0;
  let unidades = 0;
  let valor = 0;
  for (const item of pendentes.value) {
    const c = conferencia.value[item.id];
    const qtd = Number(c?.chegou) || 0;
    if (qtd <= 0) continue;
    itens += 1;
    unidades += qtd * item.fator;
    valor += qtd * Math.round((c?.custoReais ?? 0) * 100);
  }
  return { itens, unidades, valor };
});

function custoMudou(item: PedidoItemRead): boolean {
  const c = conferencia.value[item.id];
  return podeVerCusto.value && item.custo_unitario != null && c?.custoReais != null
    && Math.round(c.custoReais * 100) !== item.custo_unitario;
}

const vaiFicarFaltando = computed(() =>
  pendentes.value.some((i) => (Number(conferencia.value[i.id]?.chegou) || 0) < i.pendente),
);

function confirmar() {
  if (!resumo.value.itens) return;
  receber.mutate(
    {
      id: props.pedido.id,
      recebimento: {
        itens: pendentes.value
          .filter((i) => (Number(conferencia.value[i.id]?.chegou) || 0) > 0)
          .map((i) => {
            const c = conferencia.value[i.id];
            return {
              pedido_item_id: i.id,
              quantidade: Math.round(Number(c.chegou)),
              custo_unitario: podeVerCusto.value && c.custoReais != null ? Math.round(c.custoReais * 100) : null,
            };
          }),
        numero_nota: numeroNota.value.trim() || null,
        observacao: observacao.value.trim() || null,
        lancar_contas_pagar: lancarContas.value,
        encerrar_saldo: encerrarSaldo.value && vaiFicarFaltando.value,
      },
    },
    { onSuccess: (pedido) => emit('concluido', pedido) },
  );
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-lg font-semibold text-zinc-800">{{ pedido.codigo }} · {{ pedido.fornecedor_nome }}</p>
        <p class="text-xs text-zinc-500">Entrega prevista: {{ formatDataPura(pedido.previsao_entrega, 'a combinar') }}</p>
      </div>
      <SituacaoPedidoBadge :situacao="pedido.situacao" :atrasado="pedido.atrasado" />
    </div>

    <!-- Leitor -->
    <form class="relative" @submit.prevent="bipar">
      <ScanBarcode :size="18" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
      <input
        v-model="codigo"
        type="text"
        inputmode="numeric"
        autocomplete="off"
        autofocus
        placeholder="Bipe o código do produto ou do fardo"
        class="w-full rounded-xl border border-zinc-200 py-3 pl-10 pr-3 text-base outline-none focus:border-brand-primary"
      />
    </form>

    <!-- Itens em cartões: serve ao balcão e ao celular. -->
    <div class="flex flex-col gap-3">
      <div
        v-for="item in pendentes"
        :key="item.id"
        class="rounded-xl border p-4 transition-colors"
        :class="(conferencia[item.id]?.chegou ?? 0) >= item.pendente
          ? 'border-emerald-200 bg-emerald-50/40'
          : (conferencia[item.id]?.chegou ?? 0) > 0 ? 'border-amber-200 bg-amber-50/30' : 'border-zinc-200'"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="font-medium text-zinc-800">{{ item.descricao }}</p>
            <p class="text-xs text-zinc-500">
              Pedido {{ item.quantidade }} {{ item.unidade_compra }}<template v-if="item.fator > 1"> c/ {{ item.fator }}</template>
              <template v-if="item.quantidade_recebida"> · já chegaram {{ item.quantidade_recebida }}</template>
              · <strong class="text-zinc-700">faltam {{ item.pendente }}</strong>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 text-zinc-600 hover:bg-zinc-50 cursor-pointer"
              aria-label="Menos um"
              @click="ajustar(item, -1)"
            >
              <Minus :size="16" />
            </button>
            <input
              v-model.number="conferencia[item.id].chegou"
              type="number"
              min="0"
              :max="item.pendente"
              step="1"
              class="h-10 w-20 rounded-lg border border-zinc-200 text-center text-base font-semibold tabular-nums outline-none focus:border-brand-primary"
            />
            <button
              type="button"
              class="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 text-zinc-600 hover:bg-zinc-50 cursor-pointer"
              aria-label="Mais um"
              @click="ajustar(item, 1)"
            >
              <Plus :size="16" />
            </button>
            <span class="w-10 text-xs font-semibold text-zinc-600">{{ item.unidade_compra }}</span>
          </div>
        </div>

        <p v-if="item.fator > 1 && (conferencia[item.id]?.chegou ?? 0) > 0" class="mt-1 text-[11px] text-zinc-500">
          = {{ ((conferencia[item.id].chegou || 0) * item.fator).toLocaleString('pt-BR') }} unidades no estoque
        </p>

        <div v-if="podeVerCusto" class="mt-3 flex flex-wrap items-end gap-3">
          <div class="w-44">
            <BaseMoneyInput v-model="conferencia[item.id].custoReais" :label="`Custo real (${item.unidade_compra})`" />
          </div>
          <p v-if="custoMudou(item)" class="flex items-center gap-1 pb-2.5 text-[11px] text-amber-700">
            <AlertTriangle :size="12" />
            Diferente do pedido ({{ formatCurrency(item.custo_unitario ?? 0) }})
          </p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-2">
      <BaseInput v-model="numeroNota" label="Nº da nota (se veio em papel)" placeholder="Opcional" />
      <BaseInput v-model="observacao" label="Observação" placeholder="Ex.: 1 fardo amassado" />
    </div>

    <div class="flex flex-col gap-2 text-sm">
      <label v-if="vaiFicarFaltando" class="flex cursor-pointer items-start gap-2 text-zinc-700">
        <input v-model="encerrarSaldo" type="checkbox" class="mt-0.5 accent-brand-primary" />
        <span>
          <strong>O resto não vem mais</strong> — encerrar o saldo e fechar o pedido
          <span class="block text-xs text-zinc-500">Senão o pedido fica "recebido em parte", esperando o resto.</span>
        </span>
      </label>
      <label v-if="podeVerCusto" class="flex cursor-pointer items-start gap-2 text-zinc-700">
        <input v-model="lancarContas" type="checkbox" class="mt-0.5 accent-brand-primary" />
        <span>
          Lançar no contas a pagar
          <span class="block text-xs text-zinc-500">
            As parcelas combinadas ({{ pedido.condicao_pagamento || 'à vista' }}), proporcionais ao que chegou.
            Só com o módulo Financeiro.
          </span>
        </span>
      </label>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-100 pt-4">
      <p class="text-sm text-zinc-600">
        <template v-if="resumo.itens">
          <strong class="text-zinc-800">{{ resumo.itens }}</strong> {{ resumo.itens === 1 ? 'item' : 'itens' }} ·
          <strong class="text-zinc-800">{{ resumo.unidades.toLocaleString('pt-BR') }}</strong> unidades entram no estoque
          <template v-if="podeVerCusto"> · {{ formatCurrency(resumo.valor) }}</template>
        </template>
        <template v-else>Bipe ou digite o que chegou.</template>
      </p>
      <BaseButton
        :disabled="!resumo.itens || !podeReceber"
        :is-loading="receber.isPending.value"
        :title="podeReceber ? '' : 'Seu cargo não tem a permissão de dar entrada'"
        @click="confirmar"
      >
        Dar entrada no estoque
      </BaseButton>
    </div>
  </div>
</template>
