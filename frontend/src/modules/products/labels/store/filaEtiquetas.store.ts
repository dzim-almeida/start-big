/**
 * @fileoverview Fila de impressão de etiquetas.
 *
 * Store (e não estado da aba) porque a fila é alimentada de FORA dela: o
 * botão "Etiqueta" do card de produto adiciona e troca de aba. Guarda só o id
 * e a quantidade — nome e preço são lidos da listagem na hora de imprimir,
 * para uma alteração de preço feita com a fila montada já sair certa.
 *
 * Vive só na sessão: fila de etiqueta é trabalho do momento, não cadastro.
 */

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import type { ItemFilaEtiqueta } from '../types/etiquetas.types';

/** Teto por item: acima disto é quase certamente dígito a mais. */
export const MAX_POR_ITEM = 999;

function limitar(quantidade: number): number {
  return Math.max(1, Math.min(MAX_POR_ITEM, Math.round(quantidade) || 1));
}

export const useFilaEtiquetasStore = defineStore('filaEtiquetas', () => {
  const itens = ref<ItemFilaEtiqueta[]>([]);
  /** Painel da fila aberto. No store para quem adiciona de fora (card do produto) poder abrir. */
  const painelAberto = ref(false);

  const totalEtiquetas = computed(() => itens.value.reduce((soma, i) => soma + i.quantidade, 0));

  /** Soma à quantidade de quem já está na fila, em vez de duplicar a linha. */
  function adicionar(produtoId: number, quantidade = 1) {
    const existente = itens.value.find((i) => i.produtoId === produtoId);
    if (existente) existente.quantidade = limitar(existente.quantidade + quantidade);
    else itens.value.push({ produtoId, quantidade: limitar(quantidade) });
  }

  function definirQuantidade(produtoId: number, quantidade: number) {
    const item = itens.value.find((i) => i.produtoId === produtoId);
    if (item) item.quantidade = limitar(quantidade);
  }

  function remover(produtoId: number) {
    itens.value = itens.value.filter((i) => i.produtoId !== produtoId);
  }

  function limpar() {
    itens.value = [];
  }

  return { itens, painelAberto, totalEtiquetas, adicionar, definirQuantidade, remover, limpar };
});
