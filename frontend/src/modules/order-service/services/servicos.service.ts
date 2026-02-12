import api from '@/api/axios';

import { ServiceCreateZod, ServiceUpdateZod, PaginatedServicesZod, PaginatedServicesSchema, ServiceReadZod, ServiceStatsZod, ServiceStatsSchema } from '../schemas/servicos.schema';

import { ServicosQuerySearch } from '../types/servicos.types';

const BASE_URL = 'servicos/' as const;



export async function getServicos(query: ServicosQuerySearch): Promise<PaginatedServicesZod> {

  let request_url = `${BASE_URL}?`
  if (query.search) request_url += `search=${query.search}&`
  if (query.active !== undefined) request_url += `active=${query.active}&`
  if (query.page) request_url += `page=${query.page}&`
  if (query.limit) request_url += `limit=${query.limit}&`
  
  const { data } = await api.get<PaginatedServicesZod>(request_url);
  const parsedData = PaginatedServicesSchema.parse(data);
  return parsedData;
}

export async function createServico(servico: ServiceCreateZod): Promise<ServiceReadZod> {
  const { data } = await api.post<ServiceReadZod>(`${BASE_URL}`, servico);
  return data;
}

export async function updateServico(
  id: number,
  servico: ServiceUpdateZod,
): Promise<ServiceReadZod> {
  const { data } = await api.put<ServiceReadZod>(`${BASE_URL}${id}`, servico);
  return data;
}

export async function toggleServicoAtivo(id: number): Promise<ServiceReadZod> {
  const { data } = await api.put<ServiceReadZod>(`${BASE_URL}toggle_ativo/${id}`);
  return data;
}

export async function getServicosStats(): Promise<ServiceStatsZod> {
  const { data } = await api.get<ServiceStatsZod>(`${BASE_URL}stats`);
  return ServiceStatsSchema.parse(data);
}
