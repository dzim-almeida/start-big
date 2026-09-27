<script setup lang="ts">
import { computed } from 'vue';
import { SlidersHorizontal } from 'lucide-vue-next';
import { ProductSaleListItem, type EmbalagemPdv } from '../../schemas/productSale.schema';

import { formatCurrency } from '@/shared/utils/finance';
import { saldoEmEmbalagem } from '@/shared/utils/embalagem';

type EstoqueStatus = 'sem_estoque' | 'baixo' | 'normal';

const props = defineProps<{
    product: ProductSaleListItem[number];
    highlighted?: boolean;
}>();

const emit = defineEmits<{
  click: [];
  selectForQuantity: [];
  /** Lançar 1 fardo/caixa (só existe com embalagens ligadas). */
  embalagem: [embalagem: EmbalagemPdv];
}>();

// Fator 1 é só um código a mais da unidade (D3): não vira botão.
const embalagens = computed(() => (props.product.embalagens ?? []).filter((e) => e.fator > 1));
// "= 10 FD", discreto, ao lado do saldo em unidade (D21).
const saldoFechado = computed(() =>
  saldoEmEmbalagem(
    props.product.estoque,
    embalagens.value.map((e) => ({ ...e, ativo: true, vende_no_pdv: true })),
  ),
);

import { getBackendBaseUrl } from '@/api/backendUrl';

const estoqueStatus = computed<EstoqueStatus>(() => {
  const qty = props.product.estoque;
  if (qty <= 0) return 'sem_estoque';
  const minima = props.product.quantidade_minima;
  if (minima != null && qty <= minima) return 'baixo';
  return 'normal';
});

/**
 * Sem estoque NÃO é o mesmo que indisponível.
 *
 * Esta linha decidia sozinha que produto zerado não se vende — e decidia
 * diferente do leitor de código de barras, que abria o aviso e deixava o
 * operador escolher, e diferente da empresa, que tem `permitir_venda_estoque_
 * zerado` na configuração e não era consultada por ninguém aqui.
 *
 * Agora a linha só PINTA o estado. Quem decide se entra no carrinho é
 * `tentarAdicionarProduto`, que lê a configuração da loja e usa o mesmo limiar
 * do backend — um lugar só, para as três portas.
 */
const semEstoque = computed(() => estoqueStatus.value === 'sem_estoque');

const estoqueClasses = computed(() => {
  switch (estoqueStatus.value) {
    case 'sem_estoque': return 'bg-red-100 text-red-600';
    case 'baixo': return 'bg-orange-100 text-orange-600';
    case 'normal': return 'bg-blue-100 text-blue-600';
  }
});

function handleClick() {
  emit('click');
}

function handleSelectForQuantity() {
  emit('selectForQuantity');
}

const imgUrl = computed(() => {
    if (!props.product.imagem_url) return null;
    return `${getBackendBaseUrl()}/${props.product.imagem_url}`;
})
</script>

<template>
  <div
    :class="[
      'py-2 px-6 border-b-2 flex justify-between group transition-colors cursor-pointer',
      semEstoque ? 'bg-zinc-50/80' : 'bg-white hover:bg-zinc-100',
      highlighted ? 'bg-brand-primary/5 border-2 border-brand-primary' : 'border-zinc-200',
    ]"
    @click="handleClick"
  >
    <div class="flex-1 flex gap-4">
      <div class="w-20 h-20 rounded-2xl bg-brand-primary/30 group-hover:transition-transform group-hover:scale-105 transition-all">
        <img v-if="imgUrl" :src="imgUrl" :alt="product.nome" class="w-full h-full object-fit rounded-xl" />
        <div v-else class="w-full h-full flex items-center justify-center text-white group-hover:text-lg transition-all">
          {{ product.nome.charAt(0).toUpperCase() }}
        </div>
      </div>
      <div>
        <h1 class="font-poppins font-semibold text-md text-zinc-800 group-hover:text-brand-primary">{{ product.nome }}</h1>
        <p class="font-poppins font-semibold text-xs text-zinc-500">{{ `SKU: ${product.sku}` }}</p>
        <div v-if="embalagens.length" class="mt-1.5 flex flex-wrap items-center gap-1.5">
          <button
            v-for="emb in embalagens"
            :key="emb.id"
            type="button"
            class="px-2 py-0.5 rounded-md border border-brand-primary/30 bg-brand-primary/5 text-[11px] font-semibold text-brand-primary hover:bg-brand-primary/15 transition-colors cursor-pointer"
            :title="`Lançar 1 ${emb.descricao || emb.sigla} (${emb.fator} un)`"
            @click.stop="emit('embalagem', emb)"
          >
            {{ emb.sigla }} {{ emb.fator }} · {{ formatCurrency(emb.preco) }}
          </button>
          <span v-if="product.so_embalagem_fechada" class="text-[10px] font-semibold uppercase text-zinc-400">
            só fechada
          </span>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <div class="flex flex-col items-end gap-4">
          <p
            :class="[
              'py-1 px-3 w-fit rounded-md font-poppins font-bold text-xs',
              estoqueClasses,
            ]"
          >
            {{ `Estoque: ${product.estoque} un.` }}
            <span v-if="saldoFechado" class="font-semibold opacity-70">{{ saldoFechado }}</span>
          </p>
          <p class="font-poppins font-bold text-xl text-brand-primary">
            {{ formatCurrency(product.preco) }}
          </p>
      </div>
      <button
        type="button"
        class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
        title="Escolher quantidade e desconto"
        @click.stop="handleSelectForQuantity"
      >
        <SlidersHorizontal :size="18" />
      </button>
    </div>
  </div>
</template>
