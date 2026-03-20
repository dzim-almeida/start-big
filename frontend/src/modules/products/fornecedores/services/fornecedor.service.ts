import api from '@/api/axios';
import { FornecedorReadSchema, type FornecedorReadType } from '../schemas/fornecedor.schema';
import { z } from 'zod';

const BASE_URL = 'fornecedores' as const;

export interface FornecedorCreatePayload {
  nome: string;
  cnpj: string;
  nome_fantasia?: string;
  ie?: string;
  telefone?: string;
  celular?: string;
  email?: string;
  representante?: string;
}

export type FornecedorUpdatePayload = Partial<FornecedorCreatePayload>;

export async function getFornecedores(buscar?: string): Promise<FornecedorReadType[]> {
  const params: Record<string, string> = {};
  if (buscar) params.buscar = buscar;
  const { data } = await api.get<FornecedorReadType[]>(BASE_URL, { params });
  const result = z.array(FornecedorReadSchema).safeParse(data);
  return result.success ? result.data : (data as FornecedorReadType[]);
}

export async function createFornecedor(
  payload: FornecedorCreatePayload,
): Promise<FornecedorReadType> {
  const { data } = await api.post<FornecedorReadType>(BASE_URL, payload);
  return data;
}

export async function updateFornecedor(
  id: number,
  payload: FornecedorUpdatePayload,
): Promise<FornecedorReadType> {
  const { data } = await api.put<FornecedorReadType>(`${BASE_URL}/${id}`, payload);
  return data;
}

export async function toggleFornecedorAtivo(id: number): Promise<FornecedorReadType> {
  const { data } = await api.put<FornecedorReadType>(`${BASE_URL}/toggle_ativo/${id}`);
  return data;
}
