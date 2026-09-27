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

export function chaveDoItem(item: { produtoId: number; embalagemId: number | null }): string {
  return `${item.produtoId}:${item.embalagemId ?? 'un'}`;
}

function limitar(quantidade: number): number {
  return Math.max(1, Math.min(MAX_POR_ITEM, Math.round(quantidade) || 1));
}

export const useFilaEtiquetasStore = defineStore('filaEtiquetas', () => {
  const itens = ref<ItemFilaEtiqueta[]>([]);
  /** Painel da fila aberto. No store para quem adiciona de fora (card do produto) poder abrir. */
  const painelAberto = ref(false);

  const totalEtiquetas = computed(() => itens.value.reduce((soma, i) => soma + i.quantidade, 0));

  const achar = (chave: string) => itens.value.find((i) => chaveDoItem(i) === chave);

  /** Soma à quantidade de quem já está na fila, em vez de duplicar a linha. */
  function adicionar(produtoId: number, quantidade = 1, embalagemId: number | null = null) {
    const existente = achar(chaveDoItem({ produtoId, embalagemId }));
    if (existente) existente.quantidade = limitar(existente.quantidade + quantidade);
    else itens.value.push({ produtoId, quantidade: limitar(quantidade), embalagemId });
  }

  function definirQuantidade(chave: string, quantidade: number) {
    const item = achar(chave);
    if (item) item.quantidade = limitar(quantidade);
  }

  function remover(chave: string) {
    itens.value = itens.value.filter((i) => chaveDoItem(i) !== chave);
  }

  /** Troca unidade ↔ fardo numa linha; se a outra já está na fila, soma nela. */
  function trocarEmbalagem(chave: string, embalagemId: number | null) {
    const item = achar(chave);
    if (!item || item.embalagemId === embalagemId) return;
    remover(chave);
    adicionar(item.produtoId, item.quantidade, embalagemId);
  }

  function limpar() {
    itens.value = [];
  }

  return { itens, painelAberto, totalEtiquetas, adicionar, definirQuantidade, remover, trocarEmbalagem, limpar };
});
