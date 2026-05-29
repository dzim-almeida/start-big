import api from '@/api/axios';

import { ServiceCreateZod, ServiceUpdateZod, PaginatedServicesZod, PaginatedServicesSchema, ServiceReadZod, ServiceStatsZod, ServiceStatsSchema } from '../schemas/servicos.schema';

import { ServicosQuerySearch } from '../types/servicos.types';

const BASE_URL = 'servicos' as const;

export async function getServicos(query: ServicosQuerySearch): Promise<PaginatedServicesZod> {
  const params: Record<string, string | number | boolean> = {};
  if (query.search) params.search = query.search;
  if (query.active !== undefined) params.active = query.active;
  if (query.page) params.page = query.page;
  if (query.limit) params.limit = query.limit;

  const { data } = await api.get<PaginatedServicesZod>(`${BASE_URL}/`, { params });
  return PaginatedServicesSchema.parse(data);
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

export async function getServicosStats(): Promise<ServiceStatsZod> {
  const { data } = await api.get<ServiceStatsZod>(`${BASE_URL}/stats`);
  return ServiceStatsSchema.parse(data);
}
