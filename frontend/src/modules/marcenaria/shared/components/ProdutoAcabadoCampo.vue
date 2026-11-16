<script setup lang="ts">
/**
 * @component ProdutoAcabadoCampo
 * @description Escolhe o produto acabado do faturamento dos móveis
 * (docs/marcenaria-faturamento-plano.md, D2): mostra o escolhido (nome e
 * código) e, para quem pode alterar, uma busca no cadastro de produtos para
 * trocar. O NCM e o CST são do cadastro fiscal do próprio produto.
 *
 * Usado em Configurações › Marcenaria (os dois produtos padrão) e no modal do
 * móvel do orçamento (o "tipo fiscal" daquele móvel, D3).
 */
import { computed, ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { refDebounced } from '@vueuse/core';

import { getProdutoById, getProdutos } from '@/modules/products/inventory/services/product.service';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';

const props = defineProps<{
  rotulo: string;
  ajuda: string;
  disabled: boolean;
  erro?: string;
  /** O que mostrar sem produto escolhido (no móvel: "o padrão da configuração"). */
  textoVazio?: string;
  /** Sem a linha de baixo (dentro de um modal, que já separa os campos). */
  semDivisoria?: boolean;
}>();

const modelo = defineModel<number | null>({ required: true });

const { data: escolhido } = useQuery({
  queryKey: computed(() => ['produto-acabado', modelo.value]),
  queryFn: () => getProdutoById(modelo.value as number),
  enabled: computed(() => modelo.value !== null),
  retry: false,
  staleTime: 60_000,
});

const trocando = ref(false);
const termo = ref('');
const termoEsperado = refDebounced(termo, 300);          // espera parar de digitar
const buscaValida = computed(() => termoEsperado.value.trim().length >= 2);

const { data: resultados } = useQuery({
  queryKey: computed(() => ['produto-acabado-busca', termoEsperado.value.trim()]),
  queryFn: () => getProdutos(termoEsperado.value.trim(), 8),
  enabled: buscaValida,
  retry: false,
  staleTime: 30_000,
});

function escolher(produto: ProdutoRead) {
  modelo.value = produto.id;
  trocando.value = false;
  termo.value = '';
}
</script>

<template>
  <div :class="props.semDivisoria ? '' : 'py-3 border-b border-zinc-100'">
    <label class="text-xs font-medium text-zinc-600">{{ props.rotulo }}</label>
    <p class="text-[11px] text-zinc-400 mt-0.5">{{ props.ajuda }}</p>

    <div class="mt-2 flex flex-wrap items-center gap-3">
      <span v-if="modelo !== null && escolhido" class="text-sm text-zinc-800" data-testid="produto-escolhido">
        {{ escolhido.nome }} <span class="text-xs text-zinc-400">({{ escolhido.codigo_produto }})</span>
      </span>
      <span v-else-if="modelo === null" class="text-sm text-zinc-400">{{ props.textoVazio ?? 'Nenhum produto escolhido' }}</span>
      <button
        v-if="!props.disabled && !trocando"
        type="button"
        class="text-xs font-medium text-brand-primary hover:underline"
        @click="trocando = true"
      >
        {{ modelo === null ? 'Escolher produto' : 'Trocar' }}
      </button>
      <button
        v-if="!props.disabled && !trocando && modelo !== null && props.textoVazio"
        type="button"
        class="text-xs text-zinc-500 hover:underline"
        @click="modelo = null"
      >
        Usar o padrão
      </button>
    </div>

    <div v-if="trocando && !props.disabled" class="mt-2 max-w-sm">
      <input
        v-model="termo"
        type="text"
        placeholder="Nome ou código do produto"
        class="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm text-zinc-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary"
        data-testid="busca-produto-acabado"
      />
      <ul v-if="buscaValida && resultados?.length" class="mt-1 border border-zinc-200 rounded-lg divide-y divide-zinc-100 bg-white">
        <li v-for="produto in resultados" :key="produto.id">
          <button type="button" class="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50" @click="escolher(produto)">
            {{ produto.nome }} <span class="text-xs text-zinc-400">({{ produto.codigo_produto }})</span>
          </button>
        </li>
      </ul>
      <p v-else-if="buscaValida && resultados" class="mt-1 text-[11px] text-zinc-400">Nenhum produto encontrado.</p>
      <button type="button" class="mt-1 text-[11px] text-zinc-500 hover:underline" @click="trocando = false">Cancelar</button>
    </div>

    <p v-if="props.erro" class="text-[11px] text-red-600 mt-1">{{ props.erro }}</p>
  </div>
</template>
