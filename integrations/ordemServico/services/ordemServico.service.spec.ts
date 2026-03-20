import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { ordemServicoService, OSServiceError } from './ordemServico.service';
import api from '@/shared/libs/axios';
import type { OrdemServicoCreate, OrdemServicoRead } from '../types/ordemServico.types';

vi.mock('@/shared/libs/axios');

const mockApi = api as unknown as {
  get: Mock;
  post: Mock;
  put: Mock;
  delete: Mock;
};

describe('OrdemServicoService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('create', () => {
    it('should create an OS and return transformed data', async () => {
      const mockResponse: OrdemServicoRead = {
        id: 1,
        numero: 'OS-2024-0001',
        cliente_id: 1,
        status: 'ABERTA',
        prioridade: 'NORMAL',
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        valor_total: 15000,
        desconto: 0,
        valor_entrada: 0,
        data_criacao: '2024-01-15T10:00:00Z',
        data_atualizacao: '2024-01-15T10:00:00Z',
        ativo: true,
        itens: [],
        pagamentos: [],
        fotos: [],
      };

      mockApi.post.mockResolvedValue({ data: mockResponse });

      const createData: OrdemServicoCreate = {
        cliente_id: 1,
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
      };

      const result = await ordemServicoService.create(createData);

      expect(mockApi.post).toHaveBeenCalledWith('/ordens-servico', createData);
      expect(result.id).toBe(1);
      expect(result.data_criacao).toBeInstanceOf(Date);
    });

    it('should throw OSServiceError on failure', async () => {
      mockApi.post.mockRejectedValue({
        response: { status: 400, data: { detail: 'Dados inválidos' } },
      });

      const createData: OrdemServicoCreate = {
        cliente_id: 1,
        equipamento: '',
        defeito_relatado: '',
      };

      await expect(ordemServicoService.create(createData)).rejects.toThrow(OSServiceError);
    });
  });

  describe('getAll', () => {
    it('should fetch paginated OS list', async () => {
      const mockResponse = {
        items: [
          {
            id: 1,
            numero: 'OS-2024-0001',
            cliente_id: 1,
            status: 'ABERTA',
            prioridade: 'NORMAL',
            equipamento: 'iPhone 12',
            defeito_relatado: 'Tela quebrada',
            valor_total: 15000,
            data_criacao: '2024-01-15T10:00:00Z',
            ativo: true,
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
        pages: 1,
      };

      mockApi.get.mockResolvedValue({ data: mockResponse });

      const result = await ordemServicoService.getAll({ page: 1, limit: 10 });

      expect(mockApi.get).toHaveBeenCalledWith('/ordens-servico', {
        params: { page: 1, limit: 10 },
      });
      expect(result.items).toHaveLength(1);
      expect(result.items[0].data_criacao).toBeInstanceOf(Date);
    });

    it('should filter out empty and "todos" params', async () => {
      mockApi.get.mockResolvedValue({
        data: { items: [], total: 0, page: 1, limit: 10, pages: 0 },
      });

      await ordemServicoService.getAll({
        status: 'todos',
        buscar: '',
        page: 1,
      });

      expect(mockApi.get).toHaveBeenCalledWith('/ordens-servico', {
        params: { page: 1 },
      });
    });
  });

  describe('getById', () => {
    it('should fetch OS by id', async () => {
      const mockResponse: OrdemServicoRead = {
        id: 1,
        numero: 'OS-2024-0001',
        cliente_id: 1,
        status: 'ABERTA',
        prioridade: 'NORMAL',
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        valor_total: 15000,
        desconto: 0,
        valor_entrada: 0,
        data_criacao: '2024-01-15T10:00:00Z',
        data_atualizacao: '2024-01-15T10:00:00Z',
        ativo: true,
        itens: [],
        pagamentos: [],
        fotos: [],
      };

      mockApi.get.mockResolvedValue({ data: mockResponse });

      const result = await ordemServicoService.getById(1);

      expect(mockApi.get).toHaveBeenCalledWith('/ordens-servico/1');
      expect(result.id).toBe(1);
    });

    it('should throw OSServiceError when OS not found', async () => {
      mockApi.get.mockRejectedValue({
        response: { status: 404, data: { detail: 'OS não encontrada' } },
      });

      await expect(ordemServicoService.getById(999)).rejects.toThrow(OSServiceError);
    });
  });

  describe('update', () => {
    it('should update OS', async () => {
      const mockResponse: OrdemServicoRead = {
        id: 1,
        numero: 'OS-2024-0001',
        cliente_id: 1,
        status: 'EM_ANDAMENTO',
        prioridade: 'ALTA',
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        valor_total: 15000,
        desconto: 0,
        valor_entrada: 0,
        data_criacao: '2024-01-15T10:00:00Z',
        data_atualizacao: '2024-01-15T11:00:00Z',
        ativo: true,
        itens: [],
        pagamentos: [],
        fotos: [],
      };

      mockApi.put.mockResolvedValue({ data: mockResponse });

      const result = await ordemServicoService.update(1, {
        status: 'EM_ANDAMENTO',
        prioridade: 'ALTA',
      });

      expect(mockApi.put).toHaveBeenCalledWith('/ordens-servico/1', {
        status: 'EM_ANDAMENTO',
        prioridade: 'ALTA',
      });
      expect(result.status).toBe('EM_ANDAMENTO');
    });
  });

  describe('finalizar', () => {
    it('should finalize OS', async () => {
      const mockResponse: OrdemServicoRead = {
        id: 1,
        numero: 'OS-2024-0001',
        cliente_id: 1,
        status: 'FINALIZADA',
        prioridade: 'NORMAL',
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        solucao: 'Tela substituída',
        valor_total: 15000,
        desconto: 0,
        valor_entrada: 0,
        data_criacao: '2024-01-15T10:00:00Z',
        data_atualizacao: '2024-01-15T12:00:00Z',
        data_finalizacao: '2024-01-15T12:00:00Z',
        ativo: true,
        itens: [],
        pagamentos: [],
        fotos: [],
      };

      mockApi.put.mockResolvedValue({ data: mockResponse });

      const result = await ordemServicoService.finalizar(1, {
        solucao: 'Tela substituída',
        pagamentos: [{ forma_pagamento_id: 1, valor: 15000, parcelas: 1 }],
      });

      expect(mockApi.put).toHaveBeenCalledWith('/ordens-servico/1/finalizar', {
        solucao: 'Tela substituída',
        pagamentos: [{ forma_pagamento_id: 1, valor: 15000, parcelas: 1 }],
      });
      expect(result.status).toBe('FINALIZADA');
    });
  });

  describe('cancelar', () => {
    it('should cancel OS with reason', async () => {
      const mockResponse: OrdemServicoRead = {
        id: 1,
        numero: 'OS-2024-0001',
        cliente_id: 1,
        status: 'CANCELADA',
        prioridade: 'NORMAL',
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        valor_total: 0,
        desconto: 0,
        valor_entrada: 0,
        data_criacao: '2024-01-15T10:00:00Z',
        data_atualizacao: '2024-01-15T12:00:00Z',
        ativo: true,
        itens: [],
        pagamentos: [],
        fotos: [],
      };

      mockApi.put.mockResolvedValue({ data: mockResponse });

      const result = await ordemServicoService.cancelar(1, 'Cliente desistiu');

      expect(mockApi.put).toHaveBeenCalledWith('/ordens-servico/1/cancelar', {
        motivo: 'Cliente desistiu',
      });
      expect(result.status).toBe('CANCELADA');
    });
  });

  describe('reabrir', () => {
    it('should reopen OS', async () => {
      const mockResponse: OrdemServicoRead = {
        id: 1,
        numero: 'OS-2024-0001',
        cliente_id: 1,
        status: 'EM_ANDAMENTO',
        prioridade: 'NORMAL',
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        valor_total: 15000,
        desconto: 0,
        valor_entrada: 0,
        data_criacao: '2024-01-15T10:00:00Z',
        data_atualizacao: '2024-01-15T13:00:00Z',
        ativo: true,
        itens: [],
        pagamentos: [],
        fotos: [],
      };

      mockApi.put.mockResolvedValue({ data: mockResponse });

      const result = await ordemServicoService.reabrir(1);

      expect(mockApi.put).toHaveBeenCalledWith('/ordens-servico/1/reabrir');
      expect(result.status).toBe('EM_ANDAMENTO');
    });
  });

  describe('getEstatisticas', () => {
    it('should fetch statistics', async () => {
      const mockStats = {
        ABERTA: 5,
        EM_ANDAMENTO: 3,
        FINALIZADA: 10,
        CANCELADA: 2,
      };

      mockApi.get.mockResolvedValue({ data: mockStats });

      const result = await ordemServicoService.getEstatisticas();

      expect(mockApi.get).toHaveBeenCalledWith('/ordens-servico/estatisticas');
      expect(result).toEqual(mockStats);
    });
  });

  describe('uploadFoto', () => {
    it('should upload photo', async () => {
      const mockResponse = { id: 1, url: '/uploads/foto.jpg' };
      mockApi.post.mockResolvedValue({ data: mockResponse });

      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
      const result = await ordemServicoService.uploadFoto(1, file);

      expect(mockApi.post).toHaveBeenCalledWith(
        '/ordens-servico-fotos/1',
        expect.any(FormData),
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteFoto', () => {
    it('should delete photo', async () => {
      mockApi.delete.mockResolvedValue({});

      await ordemServicoService.deleteFoto(1);

      expect(mockApi.delete).toHaveBeenCalledWith('/ordens-servico-fotos/1');
    });
  });
});
