// ============================================================================
// MÓDULO: FornecedorService (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Centralizar as requisições HTTP (Axios) para o recurso de 
//                   fornecedores, transportadoras e entregadores.
// FUNCIONALIDADES: Busca com filtros, criação, atualização parcial/total e 
//                  toggle de status ativo/inativo com validação de Schema.
// ============================================================================
import api from '@/api/axios';
import { FornecedorReadSchema, type FornecedorReadType } from '../schemas/fornecedor.schema';
import { z } from 'zod';

const BASE_URL = 'fornecedores' as const;

interface EnderecoPayload {
  id?: number;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  estado?: string;
  cep: string;
}

export interface FornecedorCreatePayload {
  tipo?: string;
  nome: string;
  cnpj?: string;
  cpf?: string;
  nome_fantasia?: string;
  ie?: string;
  telefone?: string;
  celular?: string;
  email?: string;
  representante?: string;
  veiculo?: string;
  placa?: string;
  observacao?: string;
  banco?: string;
  agencia?: string;
  conta?: string;
  tipo_conta?: string;
  pix?: string;
  endereco?: EnderecoPayload[];
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
