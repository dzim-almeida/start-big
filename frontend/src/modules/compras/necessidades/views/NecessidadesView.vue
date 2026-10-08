<script setup lang="ts">
/**
 * O que precisa ser comprado (módulo Compras, fase 2).
 *
 * A lista vem pronta do servidor (`services/compras/necessidades.py`): só entra
 * produto com estoque mínimo cadastrado, e o que está A CAMINHO já descontou.
 * Aqui o lojista só confere: marca, ajusta a quantidade, troca de fornecedor se
 * quiser, e gera um rascunho por fornecedor.
 *
 * Rascunho NÃO desconta (um rascunho esquecido sumiria com a necessidade), mas
 * a linha avisa "já em rascunho" e nasce DESMARCADA — gerar de novo sem querer
 * seria pedir duas vezes.
 *
 * "Considerar as vendas" (fase 5) soma a média de venda dos últimos 90 dias:
 * entra também quem não tem mínimo cadastrado mas gira, e a quantidade cobre o
 * prazo do fornecedor mais os dias escolhidos. Desligado, é a regra do mínimo.
 */
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { AlertTriangle, PackageCheck, ShoppingCart, TrendingDown, TrendingUp } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useAcessoCompras } from '../../shared/composables/useAcessoCompras';
import { useGerarPedidos, useNecessidadesQuery } from '../../shared/composables/useCompras';
import type { BaseNecessidade, NecessidadeItem, OpcaoFornecedor } from '../../shared/types/compras.types';

const router = useRouter();
const { podeGerenciar, podeVerCusto } = useAcessoCompras();

const pelasVendas = ref(false);
const cobertura = ref(30);
const COBERTURAS = [15, 30, 45, 60, 90];
const params = computed(() => ({
  base: (pelasVendas.value ? 'VENDAS' : 'MINIMO') as BaseNecessidade,
  cobertura_dias: cobertura.value,
}));
const { data: grupos, isLoading, isError } = useNecessidadesQuery(params);
const gerar = useGerarPedidos();

interface Escolha {
  marcado: boolean;
  quantidade: number;
  fornecedorId: number | null;
}

/** O que o lojista mexeu, por produto. Repovoa quando a lista muda. */
const escolhas = ref<Record<number, Escolha>>({});

// Trocar a base muda a sugestão: as escolhas recomeçam da nova lista.
watch(params, () => { escolhas.value = {}; });

watch(
  grupos,
  (lista) => {
    const novas: Record<number, Escolha> = {};
    for (const g of lista ?? []) {
      for (const item of g.itens) {
        const anterior = escolhas.value[item.produto_id];
        novas[item.produto_id] = anterior ?? {
          marcado: !!item.fornecedor_id && item.rascunhos.length === 0,
          quantidade: item.sugestao,
          fornecedorId: item.fornecedor_id,
        };
      }
    }
    escolhas.value = novas;
  },
  { immediate: true },
);

function opcaoEscolhida(item: NecessidadeItem): OpcaoFornecedor | undefined {
  const id = escolhas.value[item.produto_id]?.fornecedorId;
  return item.opcoes.find((o) => o.fornecedor_id === id);
}

/** Unidade de compra e fator conforme o fornecedor escolhido na linha. */
function unidadeDaLinha(item: NecessidadeItem): { sigla: string; fator: number } {
  const opcao = opcaoEscolhida(item);
  if (opcao) return { sigla: opcao.unidade_compra, fator: opcao.fator };
  return { sigla: item.unidade_compra, fator: item.fator };
}

function precoDaLinha(item: NecessidadeItem): number | null {
  const opcao = opcaoEscolhida(item);
  return opcao ? opcao.ultimo_preco : item.ultimo_preco;
}

function usarAlternativa(item: NecessidadeItem) {
  const alt = item.alternativa;
  const escolha = escolhas.value[item.produto_id];
  if (!alt || !escolha) return;
  const atual = unidadeDaLinha(item);
  escolha.fornecedorId = alt.fornecedor_id;
  // Mantém as UNIDADES do produto: 5 fardos de 12 viram 60 avulsas, não 5.
  const nova = unidadeDaLinha(item);
  escolha.quantidade = Math.max(1, Math.ceil((escolha.quantidade * atual.fator) / nova.fator));
}

function formatQtd(n: number): string {
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 3 });
}

function percentual(bp: number): string {
  return `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

const selecionados = computed(() =>
  (grupos.value ?? []).flatMap((g) =>
    g.itens
      .map((item) => ({ item, escolha: escolhas.value[item.produto_id] }))
      .filter(({ escolha }) => escolha?.marcado && escolha.fornecedorId && escolha.quantidade > 0),
  ),
);

const fornecedoresSelecionados = computed(
  () => new Set(selecionados.value.map(({ escolha }) => escolha.fornecedorId)).size,
);

const totalEstimado = computed(() =>
  selecionados.value.reduce((soma, { item, escolha }) => soma + (precoDaLinha(item) ?? 0) * escolha.quantidade, 0),
);

function marcarGrupo(itens: NecessidadeItem[], valor: boolean) {
  for (const item of itens) {
    const escolha = escolhas.value[item.produto_id];
    if (escolha && escolha.fornecedorId) escolha.marcado = valor;
  }
}

function gerarPedidos() {
  const itens = selecionados.value.map(({ item, escolha }) => ({
    produto_id: item.produto_id,
    fornecedor_id: escolha.fornecedorId as number,
    quantidade: Math.round(escolha.quantidade),
  }));
  if (!itens.length) return;
  gerar.mutate(itens, {
    onSuccess: () => router.push({ name: 'purchases-orders', query: { situacao: 'RASCUNHO' } }),
  });
}
</script>

<template>
  <div class="flex flex-col gap-6 md:gap-8 pb-20">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <PageReview
        title="Necessidades de Compra"
        :description="pelasVendas
          ? 'Pelo estoque mínimo e pela venda dos últimos 90 dias, já descontando o que está a caminho'
          : 'Produtos abaixo do estoque mínimo, já descontando o que está a caminho'"
      />
      <div class="flex flex-wrap items-center gap-3 text-sm">
        <label class="flex cursor-pointer items-center gap-2 text-zinc-700">
          <input v-model="pelasVendas" type="checkbox" class="accent-brand-primary" />
          Considerar as vendas
        </label>
        <label v-if="pelasVendas" class="flex items-center gap-2 text-zinc-600">
          comprar para
          <select
            v-model.number="cobertura"
            class="rounded-lg border border-zinc-200 px-2 py-1.5 text-sm outline-none focus:border-brand-primary"
          >
            <option v-for="d in COBERTURAS" :key="d" :value="d">{{ d }} dias</option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="isLoading" class="rounded-2xl border border-zinc-200 bg-white p-10 text-center text-sm text-zinc-400">
      Calculando o que falta…
    </div>
    <div v-else-if="isError" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
      Não foi possível carregar as necessidades. Tente de novo em instantes.
    </div>

    <!-- Nada a comprar: diz POR QUE, senão parece defeito numa loja que ainda
         não cadastrou estoque mínimo em produto nenhum. -->
    <div
      v-else-if="!grupos?.length"
      class="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-zinc-200 bg-white p-10 text-center"
    >
      <PackageCheck :size="28" class="text-emerald-500" />
      <p class="font-semibold text-zinc-800">Nada para comprar agora</p>
      <p class="max-w-md text-sm text-zinc-500">
        Só aparecem aqui os produtos com <strong>estoque mínimo</strong> cadastrado que chegaram nele<template
          v-if="pelasVendas"> — ou que vendem e vão acabar antes de o pedido chegar</template>. Cadastre o
        mínimo (e o ideal) no estoque de cada produto que a loja repõe.
      </p>
    </div>

    <template v-else>
      <section
        v-for="grupo in grupos"
        :key="grupo.fornecedor_id ?? 'sem'"
        class="overflow-hidden rounded-2xl border border-zinc-200 bg-white"
      >
        <header class="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 px-5 py-3">
          <div>
            <p class="font-semibold text-zinc-800">{{ grupo.fornecedor_nome }}</p>
            <p class="text-xs text-zinc-500">
              {{ grupo.itens.length }} {{ grupo.itens.length === 1 ? 'produto' : 'produtos' }}
            </p>
          </div>
          <div v-if="grupo.fornecedor_id && podeGerenciar" class="flex items-center gap-3 text-xs">
            <button type="button" class="font-medium text-brand-primary cursor-pointer" @click="marcarGrupo(grupo.itens, true)">
              Marcar todos
            </button>
            <button type="button" class="font-medium text-zinc-500 hover:text-zinc-800 cursor-pointer" @click="marcarGrupo(grupo.itens, false)">
              Desmarcar
            </button>
          </div>
        </header>

        <div class="overflow-x-auto">
          <table class="w-full min-w-200 text-sm">
            <thead>
              <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                <th v-if="podeGerenciar" class="w-10 px-5 py-3"></th>
                <th class="px-3 py-3">Produto</th>
                <th class="px-3 py-3 text-right">Estoque</th>
                <th class="px-3 py-3 text-right">Mín. / Ideal</th>
                <th class="px-3 py-3 text-right">A caminho</th>
                <th class="px-3 py-3">Comprar</th>
                <th class="px-3 py-3">Fornecedor</th>
                <th v-if="podeVerCusto" class="px-5 py-3 text-right">Último preço</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-100">
              <tr v-for="item in grupo.itens" :key="item.produto_id" class="align-top hover:bg-zinc-50/60">
                <td v-if="podeGerenciar" class="px-5 py-3">
                  <input
                    v-model="escolhas[item.produto_id].marcado"
                    type="checkbox"
                    class="mt-1 accent-brand-primary"
                    :disabled="!escolhas[item.produto_id]?.fornecedorId"
                    :title="escolhas[item.produto_id]?.fornecedorId ? '' : 'Cadastre um fornecedor no produto'"
                  />
                </td>
                <td class="px-3 py-3">
                  <p class="font-medium text-zinc-800">{{ item.produto_nome }}</p>
                  <p v-if="item.codigo_produto" class="text-[11px] text-zinc-400">{{ item.codigo_produto }}</p>
                  <!-- Fase 5: o giro do produto, quando a base inclui as vendas. -->
                  <p v-if="item.media_diaria" class="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-zinc-500">
                    <TrendingUp :size="12" />
                    vende ~{{ formatQtd(item.media_diaria) }}/dia
                    <template v-if="item.dura_dias != null"> · o estoque dura {{ formatQtd(item.dura_dias) }} dias</template>
                    <span
                      v-if="item.origem === 'VENDAS'"
                      class="rounded-full bg-brand-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand-primary"
                    >
                      pela venda
                    </span>
                  </p>
                  <p v-if="item.rascunhos.length" class="mt-1 inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 border border-amber-200">
                    <AlertTriangle :size="10" />
                    Já em rascunho {{ item.rascunhos.join(', ') }}
                  </p>
                  <!-- D18: outro fornecedor vende mais barato por unidade. -->
                  <p
                    v-if="podeVerCusto && item.alternativa && escolhas[item.produto_id]?.fornecedorId !== item.alternativa.fornecedor_id"
                    class="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-emerald-700"
                  >
                    <TrendingDown :size="12" />
                    {{ item.alternativa.fornecedor_nome }} vende por
                    {{ formatCurrency(Math.round(item.alternativa.preco_unidade)) }}/un
                    ({{ percentual(item.alternativa.economia_bp) }} mais barato)
                    <button
                      v-if="podeGerenciar"
                      type="button"
                      class="font-semibold underline underline-offset-2 cursor-pointer"
                      @click="usarAlternativa(item)"
                    >
                      Usar
                    </button>
                  </p>
                </td>
                <td class="px-3 py-3 text-right tabular-nums" :class="item.saldo <= 0 ? 'text-rose-600 font-semibold' : 'text-zinc-700'">
                  {{ formatQtd(item.saldo) }} {{ item.unidade_medida }}
                </td>
                <td class="px-3 py-3 text-right tabular-nums text-zinc-500">
                  <template v-if="item.minimo != null">
                    {{ formatQtd(item.minimo) }}<template v-if="item.ideal"> / {{ formatQtd(item.ideal) }}</template>
                  </template>
                  <span v-else class="text-zinc-300">—</span>
                </td>
                <td class="px-3 py-3 text-right tabular-nums text-zinc-500">
                  {{ item.em_pedido ? formatQtd(item.em_pedido) : '—' }}
                </td>
                <td class="px-3 py-3">
                  <div class="flex items-center gap-2">
                    <input
                      v-model.number="escolhas[item.produto_id].quantidade"
                      type="number"
                      min="1"
                      step="1"
                      class="w-20 rounded-lg border border-zinc-200 px-2 py-1.5 text-right text-sm tabular-nums outline-none focus:border-brand-primary disabled:bg-zinc-50"
                      :disabled="!podeGerenciar"
                    />
                    <span class="text-xs font-semibold text-zinc-600">{{ unidadeDaLinha(item).sigla }}</span>
                  </div>
                  <p v-if="unidadeDaLinha(item).fator > 1" class="mt-1 text-[11px] text-zinc-400">
                    = {{ formatQtd(escolhas[item.produto_id].quantidade * unidadeDaLinha(item).fator) }} {{ item.unidade_medida }}
                  </p>
                </td>
                <td class="px-3 py-3">
                  <select
                    v-if="item.opcoes.length > 1 && podeGerenciar"
                    v-model.number="escolhas[item.produto_id].fornecedorId"
                    class="w-44 rounded-lg border border-zinc-200 px-2 py-1.5 text-sm outline-none focus:border-brand-primary"
                  >
                    <option v-for="o in item.opcoes" :key="o.fornecedor_id" :value="o.fornecedor_id">
                      {{ o.fornecedor_nome }}
                    </option>
                  </select>
                  <span v-else-if="item.fornecedor_nome" class="text-zinc-700">{{ item.fornecedor_nome }}</span>
                  <span v-else class="text-xs text-zinc-400">Cadastre um fornecedor no produto</span>
                </td>
                <td v-if="podeVerCusto" class="px-5 py-3 text-right tabular-nums text-zinc-700">
                  {{ precoDaLinha(item) != null ? formatCurrency(precoDaLinha(item) as number) : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- Barra de ação fixa: o que vai virar pedido, antes de virar. -->
    <div
      v-if="podeGerenciar && grupos?.length"
      class="sticky bottom-0 -mx-4 md:-mx-6 lg:-mx-8 flex flex-wrap items-center justify-between gap-3 border-t border-zinc-200 bg-white/95 px-4 md:px-6 lg:px-8 py-3 backdrop-blur"
    >
      <p class="text-sm text-zinc-600">
        <strong class="text-zinc-800">{{ selecionados.length }}</strong>
        {{ selecionados.length === 1 ? 'produto' : 'produtos' }} ·
        <strong class="text-zinc-800">{{ fornecedoresSelecionados }}</strong>
        {{ fornecedoresSelecionados === 1 ? 'pedido' : 'pedidos' }}
        <template v-if="podeVerCusto && totalEstimado"> · estimado {{ formatCurrency(totalEstimado) }}</template>
      </p>
      <BaseButton
        variant="primary"
        :disabled="!selecionados.length"
        :is-loading="gerar.isPending.value"
        @click="gerarPedidos"
      >
        <ShoppingCart :size="16" class="mr-1.5" /> Gerar rascunhos
      </BaseButton>
    </div>
  </div>
</template>
