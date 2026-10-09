<script setup lang="ts">
/**
 * @component InsumoBusca
 * @description Busca de insumo no cadastro de produtos (Spec 06B D26, F5, O3a).
 *
 * - Nome ou código, a partir de 2 letras, 300 ms depois da última tecla.
 * - Cada resultado: nome, código, unidade, selo "sofre perda" e, SÓ para
 *   quem vê custos, o custo pela regra O3a (última compra, senão custo médio).
 * - Produto que JÁ está no móvel não duplica: o pai leva o foco à quantidade.
 * - `Enter` escolhe o primeiro resultado.
 * - Sem resultado: "Cadastrar insumo novo" (cadastro rápido, D31).
 */
import { computed, ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { refDebounced } from '@vueuse/core';
import { Plus, Search } from 'lucide-vue-next';

import { getProdutos } from '@/modules/products/inventory/services/product.service';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';
import { formatCurrency } from '@/shared/utils/finance';

import { CHAVE_RAIZ } from '../../constants/orcamento.constants';
import { custoPelaRegraO3a, ROTULO_ORIGEM } from '../../utils/custoProduto';
import { statusDoErro } from '../../utils/erros';

const props = defineProps<{
  /** Produtos que já estão no móvel (não duplicam). */
  produtosNoMovel: number[];
  incluiCustos: boolean;
  podeCadastrar: boolean;
}>();

const emit = defineEmits<{
  escolher: [produto: ProdutoRead];
  /** O produto já está no móvel: o pai foca a quantidade da linha existente. */
  existente: [produtoId: number];
  cadastrar: [nome: string];
}>();

const termo = ref('');
const termoEsperado = refDebounced(termo, 300);          // espera parar de digitar
const buscaValida = computed(() => termoEsperado.value.trim().length >= 2);

const { data: resultados, isFetching, error } = useQuery({
  queryKey: computed(() => [CHAVE_RAIZ, 'busca-insumo', termoEsperado.value.trim()]),
  queryFn: () => getProdutos(termoEsperado.value.trim(), 20),
  enabled: buscaValida,
  retry: false,                                          // 403 não melhora repetindo
  staleTime: 30_000,
});

/** Sem a permissão de Produtos, a busca devolve 403: dizemos o porquê. */
const semPermissao = computed(() => statusDoErro(error.value) === 403);

function escolher(produto: ProdutoRead) {
  if (props.produtosNoMovel.includes(produto.id)) emit('existente', produto.id);
  else emit('escolher', produto);
  termo.value = '';                                       // pronto para o próximo insumo
}

/** Enter escolhe o primeiro resultado (§7.12). */
function escolherPrimeiro() {
  const primeiro = resultados.value?.[0];
  if (primeiro && buscaValida.value) escolher(primeiro);
}
</script>

<template>
  <div class="relative">
    <div class="relative">
      <Search :size="14" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
      <input
        v-model="termo"
        type="search"
        placeholder="Buscar no cadastro (nome ou código)…"
        aria-label="Buscar insumo no cadastro de produtos"
        class="w-full rounded-lg border border-zinc-200 py-2 pl-8 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        data-testid="busca-insumo"
        @keydown.enter.prevent="escolherPrimeiro"
      />
    </div>

    <div v-if="buscaValida" class="mt-1 max-h-60 overflow-y-auto rounded-lg border border-zinc-200 bg-white shadow-sm" data-testid="resultados-insumo">
      <p v-if="semPermissao" class="px-3 py-2 text-xs text-amber-800">
        Seu perfil não pode consultar o cadastro de produtos. Peça a permissão de Produtos ao responsável.
      </p>
      <p v-else-if="isFetching && !resultados?.length" class="px-3 py-2 text-xs text-zinc-400">Buscando…</p>
      <template v-else-if="resultados?.length">
        <button
          v-for="produto in resultados"
          :key="produto.id"
          type="button"
          class="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-zinc-50 cursor-pointer"
          :data-testid="`resultado-${produto.id}`"
          @click="escolher(produto)"
        >
          <span class="min-w-0">
            <span class="block truncate text-sm text-zinc-800">{{ produto.nome }}</span>
            <span class="text-[11px] text-zinc-400">
              {{ produto.codigo_produto }} · {{ produto.unidade_medida || 'UN' }}
              <span v-if="produto.sofre_perda" class="ml-1 rounded bg-zinc-100 px-1 text-zinc-600">sofre perda</span>
              <span v-if="produtosNoMovel.includes(produto.id)" class="ml-1 text-brand-primary">já no móvel</span>
            </span>
          </span>
          <!-- Custo só para quem vê custos (D26). -->
          <span v-if="incluiCustos" class="shrink-0 text-right text-xs tabular-nums">
            <span :class="custoPelaRegraO3a(produto).origem === 'SEM_CUSTO' ? 'text-red-600' : 'text-zinc-700'">
              {{ formatCurrency(custoPelaRegraO3a(produto).centavos) }}
            </span>
            <span class="block text-[10px] text-zinc-400">{{ ROTULO_ORIGEM[custoPelaRegraO3a(produto).origem] }}</span>
          </span>
        </button>
      </template>
      <div v-else class="flex items-center justify-between gap-2 px-3 py-2">
        <span class="text-xs text-zinc-500">Nenhum produto encontrado.</span>
        <button
          v-if="podeCadastrar"
          type="button"
          class="text-xs font-semibold text-brand-primary hover:underline cursor-pointer"
          data-testid="cadastrar-insumo"
          @click="emit('cadastrar', termo.trim())"
        >
          Cadastrar insumo novo
        </button>
      </div>
    </div>

    <button
      v-if="podeCadastrar && !buscaValida"
      type="button"
      class="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-brand-primary hover:underline cursor-pointer"
      @click="emit('cadastrar', '')"
    >
      <Plus :size="12" /> Cadastrar insumo novo
    </button>
  </div>
</template>
