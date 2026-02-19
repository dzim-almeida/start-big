import api from '@/api/axios';
import type { AxiosError } from 'axios';
import type {
  OrdemServicoCreate,
  OrdemServicoRead,
  OrdemServicoListRead,
  OrdemServicoUpdate,
  OrdemServicoFinalizar,
  OSFilters,
  FormaPagamentoRead,
} from '../types/ordemServico.types';
import {
  OrdemServicoReadSchema,
  OrdemServicoListReadSchema,
  PaginatedOrdensServicoSchema,
} from '../schemas/ordemServico.schema';
import type { ZodSchema } from 'zod';
import { getErrorMessage } from '@/shared/utils/error.utils';

// ===========================================================================
// TIPOS AUXILIARES
// ===========================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ===========================================================================
// ERROR HANDLING
// ===========================================================================

export class OSServiceError extends Error {
  constructor(
    message: string,
    public readonly operation: string,
    public readonly originalError?: AxiosError,
    public readonly isNetwork: boolean = false,
  ) {
    super(message);
    this.name = 'OSServiceError';
  }
}

function handleServiceError(error: unknown, operation: string): never {
  const axiosError = error as AxiosError;
  const isNetwork = axiosError.response === undefined;
  const message = getErrorMessage(error, `Erro ao ${operation}`);

  throw new OSServiceError(message as string, operation, axiosError, isNetwork);
}

// ===========================================================================
// VALIDATION (DEV ONLY)
// ===========================================================================

function validateResponse(data: unknown, schema: ZodSchema, context: string): void {
  if (!import.meta.env.DEV) return;
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(`[Validation] ${context}:`, result.error.format());
  }
}

class OrdemServicoService {
  private readonly BASE_URL = '/ordens-servico';

  private _transformDates<T extends OrdemServicoRead | OrdemServicoListRead>(os: T): T {
    const transformed = { ...os };
    if (transformed.data_criacao) transformed.data_criacao = new Date(transformed.data_criacao);
    if (transformed.data_previsao) transformed.data_previsao = new Date(transformed.data_previsao);

    if ('data_atualizacao' in transformed && transformed.data_atualizacao) {
      (transformed as OrdemServicoRead).data_atualizacao = new Date((transformed as OrdemServicoRead).data_atualizacao);
    }
    if ('data_finalizacao' in transformed) {
      const dataFin = (transformed as OrdemServicoRead).data_finalizacao;
      if (dataFin) {
        (transformed as OrdemServicoRead).data_finalizacao = new Date(dataFin);
      }
    }

    return transformed;
  }

  async create(data: OrdemServicoCreate): Promise<OrdemServicoRead> {
    try {
      const response = await api.post<OrdemServicoRead>(this.BASE_URL, data);
      validateResponse(response.data, OrdemServicoReadSchema, 'create');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'criar ordem de serviço');
    }
  }

  async getAll(params?: OSFilters): Promise<PaginatedResponse<OrdemServicoListRead>> {
    try {
      const cleanParams = params ? Object.fromEntries(
        Object.entries(params).filter(([_, v]) => v !== undefined && v !== '' && v !== 'todos')
      ) : {};

      const response = await api.get<PaginatedResponse<OrdemServicoListRead>>(this.BASE_URL, { params: cleanParams });
      validateResponse(response.data, PaginatedOrdensServicoSchema, 'getAll');

      return {
        ...response.data,
        items: response.data.items.map(os => this._transformDates(os)),
      };
    } catch (error) {
      handleServiceError(error, 'buscar ordens de serviço');
    }
  }

  async getById(id: number): Promise<OrdemServicoRead> {
    try {
      const response = await api.get<OrdemServicoRead>(`${this.BASE_URL}/${id}`);
      validateResponse(response.data, OrdemServicoReadSchema, 'getById');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'buscar ordem de serviço');
    }
  }

  async getByCliente(clienteId: number): Promise<OrdemServicoListRead[]> {
    try {
      const response = await api.get<OrdemServicoListRead[]>(`${this.BASE_URL}/cliente/${clienteId}`);
      response.data.forEach((os, index) => {
        validateResponse(os, OrdemServicoListReadSchema, `getByCliente[${index}]`);
      });
      return response.data.map(os => this._transformDates(os));
    } catch (error) {
      handleServiceError(error, 'buscar ordens do cliente');
    }
  }

  async getEstatisticas(): Promise<Record<string, number>> {
    try {
      const response = await api.get<Record<string, number>>(`${this.BASE_URL}/estatisticas`);
      return response.data;
    } catch (error) {
      handleServiceError(error, 'buscar estatísticas');
    }
  }

  async getNextNumber(): Promise<{ numero: string }> {
    try {
      const response = await api.get<{ numero: string }>(`${this.BASE_URL}/proximo_numero`);
      return response.data;
    } catch (error) {
      handleServiceError(error, 'buscar próximo número');
    }
  }

  async update(id: number, data: OrdemServicoUpdate): Promise<OrdemServicoRead> {
    try {
      const response = await api.put<OrdemServicoRead>(`${this.BASE_URL}/${id}`, data);
      validateResponse(response.data, OrdemServicoReadSchema, 'update');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'atualizar ordem de serviço');
    }
  }

  async finalizar(id: number, data: OrdemServicoFinalizar): Promise<OrdemServicoRead> {
    try {
      const response = await api.put<OrdemServicoRead>(`${this.BASE_URL}/${id}/finalizar`, data);
      validateResponse(response.data, OrdemServicoReadSchema, 'finalizar');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'finalizar ordem de serviço');
    }
  }

  async cancelar(id: number, motivo?: string): Promise<OrdemServicoRead> {
    try {
      const response = await api.put<OrdemServicoRead>(`${this.BASE_URL}/${id}/cancelar`, { motivo });
      validateResponse(response.data, OrdemServicoReadSchema, 'cancelar');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'cancelar ordem de serviço');
    }
  }

  async reabrir(id: number): Promise<OrdemServicoRead> {
    try {
      const response = await api.put<OrdemServicoRead>(`${this.BASE_URL}/${id}/reabrir`);
      validateResponse(response.data, OrdemServicoReadSchema, 'reabrir');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'reabrir ordem de serviço');
    }
  }

  async toggleAtivo(id: number): Promise<OrdemServicoRead> {
    try {
      const response = await api.put<OrdemServicoRead>(`${this.BASE_URL}/toggle_ativo/${id}`);
      validateResponse(response.data, OrdemServicoReadSchema, 'toggleAtivo');
      return this._transformDates(response.data);
    } catch (error) {
      handleServiceError(error, 'alterar status ativo');
    }
  }

  async uploadFoto(osId: number, file: File) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post(`/ordens-servico-fotos/${osId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      handleServiceError(error, 'enviar foto');
    }
  }

  async deleteFoto(fotoId: number): Promise<void> {
    try {
      await api.delete(`/ordens-servico-fotos/${fotoId}`);
    } catch (error) {
      handleServiceError(error, 'excluir foto');
    }
  }

  async getFormasPagamento(): Promise<FormaPagamentoRead[]> {
    // TODO: Substituir por endpoint real quando modulo financeiro existir
    return [
      { id: 1, nome: 'Dinheiro', tipo: 'DINHEIRO', ativo: true, permite_parcelamento: false },
      { id: 2, nome: 'PIX', tipo: 'PIX', ativo: true, permite_parcelamento: false },
      { id: 3, nome: 'Cartão de Crédito', tipo: 'CARTAO_CREDITO', ativo: true, permite_parcelamento: true },
      { id: 4, nome: 'Cartão de Débito', tipo: 'CARTAO_DEBITO', ativo: true, permite_parcelamento: false },
    ];
  }
}

export const ordemServicoService = new OrdemServicoService();
