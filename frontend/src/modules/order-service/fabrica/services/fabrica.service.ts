/**
 * @fileoverview API da marcenaria-fábrica (/fabrica).
 *
 * Toda rota daqui responde 403 `SEGMENTO_SEM_FABRICA` fora do segmento
 * Marcenaria — quem chama já deve ter conferido `isMarcenaria`.
 */

import api from '@/api/axios';
import type { InsumoEscrita, InsumoRead } from '../types/fabrica.types';

export async function getInsumo(produtoId: number): Promise<InsumoRead> {
  const { data } = await api.get<InsumoRead>(`fabrica/produtos/${produtoId}/insumo`);
  return data;
}

export async function salvarInsumo(produtoId: number, insumo: InsumoEscrita): Promise<InsumoRead> {
  const { data } = await api.put<InsumoRead>(`fabrica/produtos/${produtoId}/insumo`, insumo);
  return data;
}
