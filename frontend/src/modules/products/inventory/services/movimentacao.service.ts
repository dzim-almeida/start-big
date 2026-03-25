/**
 * @fileoverview API service para movimentações de estoque
 */

import api from '@/api/axios';
import type { MovimentacaoCreate, MovimentacaoRead } from '../types/products.types';

const BASE_URL = 'produtos' as const;

export async function getMovimentacoes(produto_id?: number): Promise<MovimentacaoRead[]> {
  const params: Record<string, string | number> = { limit: 200 };
  if (produto_id !== undefined) params.produto_id = produto_id;
  const { data } = await api.get<MovimentacaoRead[]>(`${BASE_URL}/movimentacoes`, { params });
  return data;
}

export async function createMovimentacao(
  produto_id: number,
  payload: MovimentacaoCreate,
): Promise<MovimentacaoRead> {
  const { data } = await api.post<MovimentacaoRead>(
    `${BASE_URL}/${produto_id}/movimentacoes`,
    payload,
  );
  return data;
}