/**
 * @fileoverview API das regras de preço por quantidade (/produtos/{id}/regras-preco)
 */

import api from '@/api/axios';
import type { RegraPrecoEscrita, RegraPrecoRead } from '../types/regrasPreco.types';

export async function getRegrasPreco(produtoId: number): Promise<RegraPrecoRead[]> {
  const { data } = await api.get<RegraPrecoRead[]>(`produtos/${produtoId}/regras-preco`);
  return data;
}

/** Replace-all: a lista inteira; o que não vier é apagado. */
export async function salvarRegrasPreco(produtoId: number, regras: RegraPrecoEscrita[]): Promise<RegraPrecoRead[]> {
  const { data } = await api.put<RegraPrecoRead[]>(`produtos/${produtoId}/regras-preco`, { regras });
  return data;
}
