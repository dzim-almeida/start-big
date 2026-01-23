/**
 * @fileoverview API service for products
 * @description Handles all produto-related API calls
 */

import api from '@/api/axios';
import type {
  ProdutoCreate,
  ProdutoRead,
  ProdutoUpdate,
} from '../types/products.types';

const BASE_URL = 'produtos';

/**
 * Lista produtos ativos ou busca por termo
 * @param buscar - Termo de busca opcional (nome ou codigo)
 */
export async function getProdutos(buscar?: string): Promise<ProdutoRead[]> {
  const params = buscar ? { buscar } : undefined;
  const { data } = await api.get<ProdutoRead[]>(`${BASE_URL}/`, { params });
  return data;
}

/**
 * Cria um novo produto com estoque inicial
 * @param produto - Dados do produto
 */
export async function createProduto(produto: ProdutoCreate): Promise<ProdutoRead> {
  const { data } = await api.post<ProdutoRead>(`${BASE_URL}/`, produto);
  return data;
}

export async function uploadProdutoImage(produtoId: number, file: File, principal = true): Promise<void> {
  const formData = new FormData();
  formData.append('image_file', file);
  formData.append('principal', String(principal));

  await api.post(
    `produtos/${produtoId}/fotos`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
}

/**
 * Atualiza um produto existente
 * @param id - ID do produto
 * @param produto - Dados para atualizar
 */
export async function updateProduto(
  id: number,
  produto: ProdutoUpdate,
): Promise<ProdutoRead> {
  const { data } = await api.put<ProdutoRead>(`${BASE_URL}/${id}`, produto);
  return data;
}

/**
 * Ativa ou desativa um produto
 * @param id - ID do produto
 */
export async function toggleProdutoAtivo(id: number): Promise<ProdutoRead> {
  const { data } = await api.put<ProdutoRead>(`${BASE_URL}/toggle_ativo/${id}`);
  return data;
}
