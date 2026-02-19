import { describe, it, expect } from 'vitest';
import {
  OrdemServicoStatusSchema,
  OrdemServicoPrioridadeSchema,
  OSFormDataSchema,
  OrdemServicoCreateSchema,
  OrdemServicoItemCreateSchema,
} from './ordemServico.schema';

describe('ordemServico.schema', () => {
  describe('OrdemServicoStatusSchema', () => {
    it('should accept valid status values', () => {
      const validStatuses = [
        'ABERTA',
        'EM_ANDAMENTO',
        'AGUARDANDO_PECAS',
        'AGUARDANDO_APROVACAO',
        'AGUARDANDO_RETIRADA',
        'FINALIZADA',
        'CANCELADA',
      ];

      validStatuses.forEach((status) => {
        expect(OrdemServicoStatusSchema.safeParse(status).success).toBe(true);
      });
    });

    it('should reject invalid status', () => {
      const result = OrdemServicoStatusSchema.safeParse('INVALID');
      expect(result.success).toBe(false);
    });
  });

  describe('OrdemServicoPrioridadeSchema', () => {
    it('should accept valid priority values', () => {
      const validPriorities = ['BAIXA', 'NORMAL', 'ALTA', 'URGENTE'];

      validPriorities.forEach((priority) => {
        expect(OrdemServicoPrioridadeSchema.safeParse(priority).success).toBe(true);
      });
    });

    it('should reject invalid priority', () => {
      const result = OrdemServicoPrioridadeSchema.safeParse('CRITICAL');
      expect(result.success).toBe(false);
    });
  });

  describe('OSFormDataSchema', () => {
    it('should validate a minimal valid form', () => {
      const validForm = {
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
        prioridade: 'NORMAL',
        status: 'ABERTA',
      };

      const result = OSFormDataSchema.safeParse(validForm);
      expect(result.success).toBe(true);
    });

    it('should reject form without equipamento', () => {
      const invalidForm = {
        equipamento: '',
        defeito_relatado: 'Tela quebrada',
        prioridade: 'NORMAL',
        status: 'ABERTA',
      };

      const result = OSFormDataSchema.safeParse(invalidForm);
      expect(result.success).toBe(false);
    });

    it('should reject form without defeito_relatado', () => {
      const invalidForm = {
        equipamento: 'iPhone 12',
        defeito_relatado: '',
        prioridade: 'NORMAL',
        status: 'ABERTA',
      };

      const result = OSFormDataSchema.safeParse(invalidForm);
      expect(result.success).toBe(false);
    });
  });

  describe('OrdemServicoCreateSchema', () => {
    it('should validate a minimal create payload', () => {
      const validPayload = {
        cliente_id: 1,
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
      };

      const result = OrdemServicoCreateSchema.safeParse(validPayload);
      expect(result.success).toBe(true);
    });

    it('should validate a complete create payload', () => {
      const validPayload = {
        cliente_id: 1,
        funcionario_id: 1,
        equipamento: 'iPhone 12',
        marca: 'Apple',
        modelo: 'A2172',
        numero_serie: 'ABC123',
        defeito_relatado: 'Tela quebrada',
        diagnostico: 'Display danificado',
        prioridade: 'ALTA',
        itens: [
          {
            descricao: 'Troca de tela',
            quantidade: 1,
            valor_unitario: 30000,
          },
        ],
      };

      const result = OrdemServicoCreateSchema.safeParse(validPayload);
      expect(result.success).toBe(true);
    });

    it('should reject payload without cliente_id', () => {
      const invalidPayload = {
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
      };

      const result = OrdemServicoCreateSchema.safeParse(invalidPayload);
      expect(result.success).toBe(false);
    });

    it('should reject payload with invalid cliente_id', () => {
      const invalidPayload = {
        cliente_id: -1,
        equipamento: 'iPhone 12',
        defeito_relatado: 'Tela quebrada',
      };

      const result = OrdemServicoCreateSchema.safeParse(invalidPayload);
      expect(result.success).toBe(false);
    });
  });

  describe('OrdemServicoItemCreateSchema', () => {
    it('should validate a valid item', () => {
      const validItem = {
        descricao: 'Troca de tela',
        quantidade: 1,
        valor_unitario: 30000,
      };

      const result = OrdemServicoItemCreateSchema.safeParse(validItem);
      expect(result.success).toBe(true);
    });

    it('should validate item with servico_id', () => {
      const validItem = {
        servico_id: 1,
        descricao: 'Troca de tela',
        quantidade: 1,
        valor_unitario: 30000,
      };

      const result = OrdemServicoItemCreateSchema.safeParse(validItem);
      expect(result.success).toBe(true);
    });

    it('should reject item with empty descricao', () => {
      const invalidItem = {
        descricao: '',
        quantidade: 1,
        valor_unitario: 30000,
      };

      const result = OrdemServicoItemCreateSchema.safeParse(invalidItem);
      expect(result.success).toBe(false);
    });

    it('should reject item with zero quantidade', () => {
      const invalidItem = {
        descricao: 'Troca de tela',
        quantidade: 0,
        valor_unitario: 30000,
      };

      const result = OrdemServicoItemCreateSchema.safeParse(invalidItem);
      expect(result.success).toBe(false);
    });

    it('should reject item with negative valor_unitario', () => {
      const invalidItem = {
        descricao: 'Troca de tela',
        quantidade: 1,
        valor_unitario: -100,
      };

      const result = OrdemServicoItemCreateSchema.safeParse(invalidItem);
      expect(result.success).toBe(false);
    });
  });
});
