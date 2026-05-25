import api from '@/api/axios';

export interface ClienteSearchResult {
  id: number;
  tipo: 'PF' | 'PJ';
  nome: string;
  nome_fantasia?: string;
  razao_social?: string;
  cpf?: string | null;
  cnpj?: string | null;
  telefone?: string | null;
  celular?: string | null;
  email?: string | null;
}

export async function searchClientes(buscar?: string): Promise<ClienteSearchResult[]> {
  const params: Record<string, string | boolean | number> = { only_active: true, limit: 100 };
  if (buscar) params.buscar = buscar;

  const response = await api.get<{ items: ClienteSearchResult[] }>('/clientes/', { params });
  return response.data.items ?? [];
}
