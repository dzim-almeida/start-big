/**
 * @fileoverview API das embalagens do produto (/produtos/{id}/embalagens)
 */

import api from '@/api/axios';
import type { EmbalagemEscrita, EmbalagemRead } from '../types/embalagens.types';

export async function getEmbalagens(produtoId: number): Promise<EmbalagemRead[]> {
  const { data } = await api.get<EmbalagemRead[]>(`produtos/${produtoId}/embalagens`);
  return data;
}

/**
 * Replace-all: a lista inteira; o que não vier é apagado. `soEmbalagemFechada`
 * mora no produto, mas é salvo junto (A3); omitido = não mexe.
 */
export async function salvarEmbalagens(
  produtoId: number,
  embalagens: EmbalagemEscrita[],
  soEmbalagemFechada?: boolean,
): Promise<EmbalagemRead[]> {
  const { data } = await api.put<EmbalagemRead[]>(`produtos/${produtoId}/embalagens`, {
    embalagens,
    ...(soEmbalagemFechada !== undefined && { so_embalagem_fechada: soEmbalagemFechada }),
  });
  return data;
}
