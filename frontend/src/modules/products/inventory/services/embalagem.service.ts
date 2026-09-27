/**
 * @fileoverview API das embalagens do produto (/produtos/{id}/embalagens)
 */

import api from '@/api/axios';
import type { EmbalagemEscrita, EmbalagemRead } from '../types/embalagens.types';

export async function getEmbalagens(produtoId: number): Promise<EmbalagemRead[]> {
  const { data } = await api.get<EmbalagemRead[]>(`produtos/${produtoId}/embalagens`);
  return data;
}

/** Replace-all: a lista inteira; o que não vier é apagado. */
export async function salvarEmbalagens(produtoId: number, embalagens: EmbalagemEscrita[]): Promise<EmbalagemRead[]> {
  const { data } = await api.put<EmbalagemRead[]>(`produtos/${produtoId}/embalagens`, { embalagens });
  return data;
}
