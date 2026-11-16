<script setup lang="ts">
/**
 * Criar ou editar um RASCUNHO de pedido de compra.
 *
 * Só rascunho chega aqui: o backend recusa editar enviado (D6). O pedido
 * enviado volta a rascunho, com motivo, pelo detalhe.
 *
 * O PREÇO VEM SOZINHO quando dá: ao pôr um produto, a tela busca os
 * fornecedores dele e preenche a embalagem e o último preço pago a ESTE
 * fornecedor. Se outro vende mais barato por unidade, a linha avisa (D18) —
 * só avisa: quem decide de quem comprar é o lojista.
 *
 * As parcelas não se digitam: saem da condição ("30/60/90") e o backend as
 * gera de novo ao salvar, então a prévia daqui é só prévia.
 */
import { computed, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { Plus, Search, Trash2, TrendingDown } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useAcessoCompras } from '../../shared/composables/useAcessoCompras';
import { useBuscaProdutoQuery, useSalvarPedido } from '../../shared/composables/useCompras';
import { comprasKeys } from '../../shared/constants/queryKeys';
import {
  getFornecedoresDoProduto,
  getFornecedoresQueVendem,
  simularParcelas,
} from '../../shared/services/compras.service';
import type {
  EmbalagemResumo,
  FornecedorDoProdutoRead,
  ParcelaSimulada,
  PedidoRead,
  ProdutoParaPedido,
} from '../../shared/types/compras.types';

const props = defineProps<{ aberto: boolean; pedido?: PedidoRead | null }>();
const emit = defineEmits<{ fechar: []; salvo: [pedido: PedidoRead] }>();

const { podeVerCusto } = useAcessoCompras();
const salvar = useSalvarPedido();

interface Linha {
  chave: number;
  produtoId: number;
  nome: string;
  unidadeProduto: string;
  /** Vazio em item que já veio do pedido: a embalagem dele fica como está. */
  embalagens: EmbalagemResumo[];
  embalagemId: number | null;
  /** Rótulo quando não dá para trocar a embalagem (item já salvo). */
  unidadeFixa: string | null;
  fator: number;
  quantidade: number;
  /** Reais, por unidade de compra. */
  precoReais: number | undefined;
  /** Fornecedores do produto, para preencher preço e avisar o mais barato. */
  fornecedores: FornecedorDoProdutoRead[];
}

let proximaChave = 1;
const fornecedorId = ref<number | ''>('');
const previsao = ref('');
const condicao = ref('');
const freteReais = ref(0);
const descontoReais = ref(0);
const observacao = ref('');
const linhas = ref<Linha[]>([]);

const editando = computed(() => !!props.pedido);

const { data: fornecedores } = useQuery({
  queryKey: comprasKeys.fornecedores(),
  queryFn: getFornecedoresQueVendem,
  enabled: computed(() => props.aberto),
  staleTime: 60_000,
});

const opcoesFornecedor = computed(() =>
  (fornecedores.value ?? []).map((f) => ({ value: f.id, label: f.nome_fantasia || f.nome })),
);

// Repovoa a cada abertura (mesmo motivo do formulário de contas a pagar).
watch(
  () => [props.aberto, props.pedido] as const,
  ([aberto]) => {
    if (!aberto) return;
    const p = props.pedido;
    fornecedorId.value = p?.fornecedor_id ?? '';
    previsao.value = p?.previsao_entrega ?? '';
    condicao.value = p?.condicao_pagamento ?? '';
    freteReais.value = (p?.frete ?? 0) / 100;
    descontoReais.value = (p?.desconto ?? 0) / 100;
    observacao.value = p?.observacao ?? '';
    termo.value = '';
    linhas.value = (p?.itens ?? [])
      .filter((i) => i.produto_id != null)
      .map((i) => ({
        chave: proximaChave++,
        produtoId: i.produto_id as number,
        nome: i.descricao,
        unidadeProduto: i.unidade_compra,
        embalagens: [],
        embalagemId: i.embalagem_id,
        unidadeFixa: i.fator > 1 ? `${i.unidade_compra} c/ ${i.fator}` : i.unidade_compra,
        fator: i.fator,
        quantidade: i.quantidade,
        precoReais: i.custo_unitario != null ? i.custo_unitario / 100 : undefined,
        fornecedores: [],
      }));
    linhas.value.forEach(carregarFornecedores);
  },
  { immediate: true },
);

// --- busca de produto ------------------------------------------------------------------
const termo = ref('');
const { data: resultados, isFetching: buscando } = useBuscaProdutoQuery(termo);

async function carregarFornecedores(linha: Linha) {
  try {
    linha.fornecedores = await getFornecedoresDoProduto(linha.produtoId);
  } catch {
    linha.fornecedores = [];
  }
}

function deste(linha: Linha): FornecedorDoProdutoRead | undefined {
  return linha.fornecedores.find((f) => f.fornecedor_id === fornecedorId.value);
}

async function adicionar(produto: ProdutoParaPedido) {
  termo.value = '';
  const existente = linhas.value.find((l) => l.produtoId === produto.id);
  if (existente) {
    existente.quantidade += 1;
    return;
  }
  const linha: Linha = {
    chave: proximaChave++,
    produtoId: produto.id,
    nome: produto.nome,
    unidadeProduto: produto.unidade_medida,
    embalagens: produto.embalagens,
    embalagemId: null,
    unidadeFixa: null,
    fator: 1,
    quantidade: 1,
    precoReais: undefined,
    fornecedores: [],
  };
  linhas.value.push(linha);
  // Pega a referência reativa (a que está dentro do array) antes de preencher.
  const reativa = linhas.value[linhas.value.length - 1];
  await carregarFornecedores(reativa);
  const cadastro = deste(reativa);
  if (cadastro) {
    reativa.embalagemId = cadastro.embalagem_id;
    reativa.fator = cadastro.fator;
    if (cadastro.ultimo_preco != null) reativa.precoReais = cadastro.ultimo_preco / 100;
  }
}

function trocarEmbalagem(linha: Linha, id: number | null) {
  linha.embalagemId = id;
  linha.fator = id == null ? 1 : (linha.embalagens.find((e) => e.id === id)?.fator ?? 1);
}

function remover(chave: number) {
  linhas.value = linhas.value.filter((l) => l.chave !== chave);
}

/** D18: outro fornecedor do produto vende mais barato por unidade. */
function maisBarato(linha: Linha): { nome: string; porUnidade: number; diferenca: number } | null {
  if (!podeVerCusto.value) return null;
  const comPreco = linha.fornecedores.filter((f) => f.preco_unidade != null && f.preco_unidade > 0);
  if (!comPreco.length) return null;
  const menor = comPreco.reduce((a, b) => ((b.preco_unidade as number) < (a.preco_unidade as number) ? b : a));
  if (menor.fornecedor_id === fornecedorId.value) return null;
  const atualPorUnidade = linha.precoReais != null && linha.fator > 0 ? (linha.precoReais * 100) / linha.fator : null;
  if (atualPorUnidade != null && atualPorUnidade <= (menor.preco_unidade as number)) return null;
  return {
    nome: menor.fornecedor_nome,
    porUnidade: menor.preco_unidade as number,
    diferenca: atualPorUnidade ? Math.round((1 - (menor.preco_unidade as number) / atualPorUnidade) * 1000) / 10 : 0,
  };
}

// --- totais e parcelas -----------------------------------------------------------------
const valorItens = computed(() =>
  linhas.value.reduce((s, l) => s + Math.round((l.precoReais ?? 0) * 100) * (Number(l.quantidade) || 0), 0),
);
const total = computed(
  () => valorItens.value + Math.round(freteReais.value * 100) - Math.round(descontoReais.value * 100),
);

const parcelas = ref<ParcelaSimulada[]>([]);
const erroCondicao = ref('');
let atraso: ReturnType<typeof setTimeout> | undefined;

watch([total, condicao, () => props.aberto], () => {
  clearTimeout(atraso);
  if (!props.aberto || !podeVerCusto.value) return;
  atraso = setTimeout(async () => {
    try {
      parcelas.value = await simularParcelas(Math.max(total.value, 0), condicao.value.trim() || null);
      erroCondicao.value = '';
    } catch (e: any) {
      parcelas.value = [];
      erroCondicao.value = e?.response?.data?.detail ?? 'Condição inválida';
    }
  }, 350);
}, { immediate: true });

// --- salvar ----------------------------------------------------------------------------
const problemas = computed(() => {
  const lista: string[] = [];
  if (!fornecedorId.value) lista.push('Escolha o fornecedor.');
  if (!linhas.value.length) lista.push('Ponha ao menos um produto.');
  if (linhas.value.some((l) => !(Number(l.quantidade) >= 1) || !Number.isInteger(Number(l.quantidade)))) {
    lista.push('Quantidade inteira, a partir de 1.');
  }
  if (total.value < 0) lista.push('O desconto é maior que o pedido.');
  if (erroCondicao.value) lista.push(erroCondicao.value);
  return lista;
});

function enviarFormulario() {
  if (problemas.value.length) return;
  salvar.mutate(
    {
      id: props.pedido?.id ?? null,
      pedido: {
        fornecedor_id: Number(fornecedorId.value),
        previsao_entrega: previsao.value || null,
        condicao_pagamento: condicao.value.trim() || null,
        frete: Math.round(freteReais.value * 100),
        desconto: Math.round(descontoReais.value * 100),
        observacao: observacao.value.trim() || null,
        itens: linhas.value.map((l) => ({
          produto_id: l.produtoId,
          embalagem_id: l.embalagemId,
          fator: l.fator,
          quantidade: Number(l.quantidade),
          custo_unitario: Math.round((l.precoReais ?? 0) * 100),
        })),
        parcelas: null,
      },
    },
    { onSuccess: (salvo) => { emit('salvo', salvo); emit('fechar'); } },
  );
}
</script>

<template>
  <BaseModal
    :is-open="aberto"
    :title="editando ? `Editar ${pedido?.codigo}` : 'Novo pedido de compra'"
    size="4xl"
    overlay
    @close="emit('fechar')"
  >
    <div class="flex flex-col gap-5">
      <div class="grid gap-4 sm:grid-cols-3">
        <div class="sm:col-span-2">
          <BaseSelect v-model="fornecedorId" :options="opcoesFornecedor" label="Fornecedor" placeholder="Escolha…" required />
        </div>
        <BaseInput v-model="previsao" type="date" label="Entrega até" />
      </div>

      <!-- Itens -->
      <div class="flex flex-col gap-3">
        <div class="relative">
          <Search :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
          <input
            v-model="termo"
            type="text"
            placeholder="Buscar produto por nome, código ou código de barras…"
            class="w-full rounded-xl border border-zinc-200 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand-primary"
          />
          <ul
            v-if="termo.trim().length >= 2"
            class="absolute z-10 mt-1 max-h-64 w-full overflow-y-auto rounded-xl border border-zinc-200 bg-white shadow-lg"
          >
            <li v-if="buscando && !resultados?.length" class="px-4 py-3 text-sm text-zinc-400">Buscando…</li>
            <li v-else-if="!resultados?.length" class="px-4 py-3 text-sm text-zinc-400">Nenhum produto encontrado.</li>
            <li v-for="p in resultados ?? []" :key="p.id">
              <button
                type="button"
                class="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm hover:bg-zinc-50 cursor-pointer"
                @click="adicionar(p)"
              >
                <span>
                  <span class="font-medium text-zinc-800">{{ p.nome }}</span>
                  <span v-if="p.codigo_produto" class="ml-2 text-[11px] text-zinc-400">{{ p.codigo_produto }}</span>
                </span>
                <span class="flex items-center gap-1 text-xs text-zinc-500">
                  estoque {{ p.saldo.toLocaleString('pt-BR') }} {{ p.unidade_medida }}
                  <Plus :size="14" class="text-brand-primary" />
                </span>
              </button>
            </li>
          </ul>
        </div>

        <div v-if="linhas.length" class="overflow-x-auto rounded-xl border border-zinc-200">
          <table class="w-full min-w-180 text-sm">
            <thead>
              <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                <th class="px-4 py-2.5">Produto</th>
                <th class="px-3 py-2.5">Compra em</th>
                <th class="px-3 py-2.5 text-right">Qtd.</th>
                <th v-if="podeVerCusto" class="px-3 py-2.5">Preço (por unidade de compra)</th>
                <th v-if="podeVerCusto" class="px-3 py-2.5 text-right">Subtotal</th>
                <th class="w-10 px-3 py-2.5"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-100">
              <tr v-for="l in linhas" :key="l.chave" class="align-top">
                <td class="px-4 py-2.5">
                  <p class="text-zinc-800">{{ l.nome }}</p>
                  <p v-if="maisBarato(l)" class="mt-1 flex items-center gap-1 text-[11px] text-emerald-700">
                    <TrendingDown :size="12" />
                    {{ maisBarato(l)!.nome }} vende por {{ formatCurrency(Math.round(maisBarato(l)!.porUnidade)) }}/un
                    <template v-if="maisBarato(l)!.diferenca">({{ maisBarato(l)!.diferenca.toLocaleString('pt-BR') }}% mais barato)</template>
                  </p>
                </td>
                <td class="px-3 py-2.5">
                  <span v-if="l.unidadeFixa" class="text-zinc-600">{{ l.unidadeFixa }}</span>
                  <select
                    v-else
                    :value="l.embalagemId ?? ''"
                    class="rounded-lg border border-zinc-200 px-2 py-1.5 text-sm outline-none focus:border-brand-primary"
                    @change="trocarEmbalagem(l, ($event.target as HTMLSelectElement).value ? Number(($event.target as HTMLSelectElement).value) : null)"
                  >
                    <option value="">{{ l.unidadeProduto }} (avulso)</option>
                    <option v-for="e in l.embalagens" :key="e.id" :value="e.id">{{ e.sigla }} com {{ e.fator }}</option>
                  </select>
                </td>
                <td class="px-3 py-2.5 text-right">
                  <input
                    v-model.number="l.quantidade"
                    type="number"
                    min="1"
                    step="1"
                    class="w-20 rounded-lg border border-zinc-200 px-2 py-1.5 text-right text-sm tabular-nums outline-none focus:border-brand-primary"
                  />
                  <p v-if="l.fator > 1" class="mt-1 text-[11px] text-zinc-400">
                    = {{ ((Number(l.quantidade) || 0) * l.fator).toLocaleString('pt-BR') }} {{ l.unidadeProduto }}
                  </p>
                </td>
                <td v-if="podeVerCusto" class="px-3 py-2.5 w-44">
                  <BaseMoneyInput v-model="l.precoReais" />
                </td>
                <td v-if="podeVerCusto" class="px-3 py-2.5 text-right tabular-nums text-zinc-700">
                  {{ formatCurrency(Math.round((l.precoReais ?? 0) * 100) * (Number(l.quantidade) || 0)) }}
                </td>
                <td class="px-3 py-2.5">
                  <button
                    type="button"
                    class="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
                    title="Tirar do pedido"
                    @click="remover(l.chave)"
                  >
                    <Trash2 :size="15" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="rounded-xl border border-dashed border-zinc-200 py-6 text-center text-sm text-zinc-400">
          Busque os produtos acima para montar o pedido.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <BaseInput v-model="condicao" label="Condição de pagamento" placeholder="Ex.: 30/60/90 ou à vista" />
        <BaseMoneyInput v-if="podeVerCusto" v-model="freteReais" label="Frete" />
        <BaseMoneyInput v-if="podeVerCusto" v-model="descontoReais" label="Desconto" />
      </div>

      <div v-if="podeVerCusto" class="flex flex-wrap items-start justify-between gap-4 rounded-xl bg-zinc-50 px-4 py-3 text-sm">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Parcelas (prévia)</p>
          <p v-if="parcelas.length" class="mt-1 text-zinc-700">
            <span v-for="(p, i) in parcelas" :key="p.numero">
              {{ p.dias === 0 ? 'à vista' : `${p.dias}d` }}: {{ formatCurrency(p.valor) }}<template v-if="i < parcelas.length - 1"> · </template>
            </span>
          </p>
          <p class="mt-1 text-[11px] text-zinc-400">Viram contas a pagar só quando a mercadoria chegar.</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-zinc-500">Total do pedido</p>
          <p class="text-lg font-semibold text-zinc-900 tabular-nums">{{ formatCurrency(Math.max(total, 0)) }}</p>
        </div>
      </div>

      <BaseTextarea v-model="observacao" label="Observação" placeholder="Vai no pedido para o fornecedor (opcional)" :rows="2" />

      <ul v-if="problemas.length" class="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 space-y-1">
        <li v-for="p in problemas" :key="p">{{ p }}</li>
      </ul>
    </div>

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <BaseButton variant="secondary" class="px-5" @click="emit('fechar')">Cancelar</BaseButton>
        <BaseButton
          class="px-5"
          :disabled="problemas.length > 0"
          :is-loading="salvar.isPending.value"
          @click="enviarFormulario"
        >
          {{ editando ? 'Salvar rascunho' : 'Criar rascunho' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
