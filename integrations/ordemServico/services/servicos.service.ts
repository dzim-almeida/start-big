import api from '@/shared/libs/axios';
import type { PaginatedResponse } from '@/shared/types/axios.types';
import type { ServicoCreate, ServicoRead, ServicoUpdate } from '../types/servicos.types';
import { ServicoReadSchema, PaginatedServicosSchema } from '../schemas/servicos.schema';
import type { ZodSchema } from 'zod';

export interface ServicoFilters {
  buscar?: string;
  status?: 'todos' | 'ativos' | 'inativos';
  page?: number;
  limit?: number;
}

export interface ServicosStats {
  total: number;
  ativos: number;
  inativos: number;
  media_valor: number;
}

class ServicosService {
  private readonly BASE_URL = '/servicos';

  private validateResponse(data: unknown, schema: ZodSchema, context: string): void {
    if (!import.meta.env.DEV) return;

    const result = schema.safeParse(data);
    if (!result.success) {
      console.warn(`[Zod Validation] ${context}:`, result.error.format());
      console.warn('[Zod Validation] Dados recebidos:', data);
    }
  }

  private cleanFilters(filters?: ServicoFilters): Record<string, unknown> {
    if (!filters) return {};
    return Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '' && v !== 'todos')
    );
  }

  async create(data: ServicoCreate): Promise<ServicoRead> {
    const response = await api.post<ServicoRead>(this.BASE_URL, data);
    this.validateResponse(response.data, ServicoReadSchema, 'create');
    return response.data;
  }

  async getAll(filters?: ServicoFilters): Promise<PaginatedResponse<ServicoRead>> {
    const params = this.cleanFilters(filters);
    const response = await api.get<PaginatedResponse<ServicoRead>>(this.BASE_URL, { params });
    this.validateResponse(response.data, PaginatedServicosSchema, 'getAll');
    return response.data;
  }

  async update(id: number, data: ServicoUpdate): Promise<ServicoRead> {
    const response = await api.put<ServicoRead>(`${this.BASE_URL}/${id}`, data);
    this.validateResponse(response.data, ServicoReadSchema, 'update');
    return response.data;
  }

  async toggleAtivo(id: number): Promise<ServicoRead> {
    const response = await api.put<ServicoRead>(`${this.BASE_URL}/toggle_ativo/${id}`);
    this.validateResponse(response.data, ServicoReadSchema, 'toggleAtivo');
    return response.data;
  }

  async getEstatisticas(): Promise<ServicosStats> {
    const response = await api.get<ServicosStats>(`${this.BASE_URL}/estatisticas`);
    return response.data;
  }
}

export const servicosService = new ServicosService();

// Exports legados para compatibilidade
export const createServico = (data: ServicoCreate) => servicosService.create(data);
export const getServicos = (filters?: ServicoFilters) => servicosService.getAll(filters);
export const updateServico = (id: number, data: ServicoUpdate) => servicosService.update(id, data);
export const toggleServicoAtivo = (id: number) => servicosService.toggleAtivo(id);
export const getServicosEstatisticas = () => servicosService.getEstatisticas();
