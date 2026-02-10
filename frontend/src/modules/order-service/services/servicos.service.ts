import api from '@/api/axios';

import type { PaginatedResponse } from '@/shared/types/axios.types';

import { ServiceCreateZod, ServiceUpdateZod, ServiceReadZod } from '../schemas/servicos.schema';

const BASE_URL = 'servicos' as const;

type ServicosListResponse = ServiceReadZod[] | PaginatedResponse<ServiceReadZod>;


function normalizeServicosListResponse(data: ServicosListResponse): ServiceReadZod[] {
  return Array.isArray(data) ? data : data.items;
}

export async function getServicos(): Promise<ServiceReadZod[]> {
  const { data } = await api.get<ServicosListResponse>(`${BASE_URL}/`);
  return normalizeServicosListResponse(data);
}

export async function createServico(servico: ServiceCreateZod): Promise<ServiceReadZod> {
  const { data } = await api.post<ServiceReadZod>(`${BASE_URL}/`, servico);
  return data;
}

export async function updateServico(
  id: number,
  servico: ServiceUpdateZod,
): Promise<ServiceReadZod> {
  const { data } = await api.put<ServiceReadZod>(`${BASE_URL}/${id}`, servico);
  return data;
}

export async function toggleServicoAtivo(id: number): Promise<ServiceReadZod> {
  const { data } = await api.put<ServiceReadZod>(`${BASE_URL}/toggle_ativo/${id}`);
  return data;
}
