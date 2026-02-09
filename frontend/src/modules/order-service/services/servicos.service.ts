import api from '@/api/axios';
import { ENDPOINT_PERMISSION_MAP } from '@/shared/constants/permissions.constants';
import type { PaginatedResponse } from '@/shared/types/axios.types';
import type {
  ServicoCreate,
  ServicoFilters,
  ServicoRead,
  ServicosStats,
  ServicoUpdate,
} from '../types/servicos.types';

const BASE_URL = 'servicos' as const;
export const SERVICOS_PERMISSION = ENDPOINT_PERMISSION_MAP[BASE_URL];

type ServicosListResponse = ServicoRead[] | PaginatedResponse<ServicoRead>;

function cleanFilters(filters?: ServicoFilters): Record<string, unknown> {
  if (!filters) return {};

  return Object.fromEntries(
    Object.entries(filters).filter(
      ([_, value]) => value !== undefined && value !== '' && value !== 'todos',
    ),
  );
}

function normalizeServicosListResponse(data: ServicosListResponse): ServicoRead[] {
  return Array.isArray(data) ? data : data.items;
}

export async function getServicos(filters?: ServicoFilters): Promise<ServicoRead[]> {
  const params = cleanFilters(filters);
  const { data } = await api.get<ServicosListResponse>(`${BASE_URL}/`, { params });
  return normalizeServicosListResponse(data);
}

export async function createServico(servico: ServicoCreate): Promise<ServicoRead> {
  const { data } = await api.post<ServicoRead>(`${BASE_URL}/`, servico);
  return data;
}

export async function updateServico(
  id: number,
  servico: ServicoUpdate,
): Promise<ServicoRead> {
  const { data } = await api.put<ServicoRead>(`${BASE_URL}/${id}`, servico);
  return data;
}

export async function toggleServicoAtivo(id: number): Promise<ServicoRead> {
  const { data } = await api.put<ServicoRead>(`${BASE_URL}/toggle_ativo/${id}`);
  return data;
}

export async function getServicosEstatisticas(): Promise<ServicosStats> {
  const { data } = await api.get<ServicosStats>(`${BASE_URL}/estatisticas`);
  return data;
}
