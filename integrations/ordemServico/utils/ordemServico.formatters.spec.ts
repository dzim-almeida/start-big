import { describe, it, expect } from 'vitest';
import {
  getStatusLabel,
  getStatusColor,
  getPrioridadeLabel,
  getPrioridadeColor,
  getClienteNome,
  formatOSNumber,
  formatDataEntrada,
  formatDataPrevisao,
} from './ordemServico.formatters';
import type { ClienteResumo } from '../types/ordemServico.types';

describe('ordemServico.formatters', () => {
  describe('getStatusLabel', () => {
    it('should return correct label for ABERTA', () => {
      expect(getStatusLabel('ABERTA')).toBe('Aberta');
    });

    it('should return correct label for EM_ANDAMENTO', () => {
      expect(getStatusLabel('EM_ANDAMENTO')).toBe('Em Andamento');
    });

    it('should return correct label for AGUARDANDO_PECAS', () => {
      expect(getStatusLabel('AGUARDANDO_PECAS')).toBe('Aguardando Peças');
    });

    it('should return correct label for FINALIZADA', () => {
      expect(getStatusLabel('FINALIZADA')).toBe('Finalizada');
    });

    it('should return correct label for CANCELADA', () => {
      expect(getStatusLabel('CANCELADA')).toBe('Cancelada');
    });

    it('should return status value for unknown status', () => {
      expect(getStatusLabel('UNKNOWN' as any)).toBe('UNKNOWN');
    });
  });

  describe('getStatusColor', () => {
    it('should return blue for ABERTA', () => {
      expect(getStatusColor('ABERTA')).toBe('blue');
    });

    it('should return yellow for EM_ANDAMENTO', () => {
      expect(getStatusColor('EM_ANDAMENTO')).toBe('yellow');
    });

    it('should return green for FINALIZADA', () => {
      expect(getStatusColor('FINALIZADA')).toBe('green');
    });

    it('should return red for CANCELADA', () => {
      expect(getStatusColor('CANCELADA')).toBe('red');
    });

    it('should return gray for unknown status', () => {
      expect(getStatusColor('UNKNOWN' as any)).toBe('gray');
    });
  });

  describe('getPrioridadeLabel', () => {
    it('should return correct label for BAIXA', () => {
      expect(getPrioridadeLabel('BAIXA')).toBe('Baixa');
    });

    it('should return correct label for NORMAL', () => {
      expect(getPrioridadeLabel('NORMAL')).toBe('Normal');
    });

    it('should return correct label for ALTA', () => {
      expect(getPrioridadeLabel('ALTA')).toBe('Alta');
    });

    it('should return correct label for URGENTE', () => {
      expect(getPrioridadeLabel('URGENTE')).toBe('Urgente');
    });
  });

  describe('getPrioridadeColor', () => {
    it('should return gray for BAIXA', () => {
      expect(getPrioridadeColor('BAIXA')).toBe('gray');
    });

    it('should return blue for NORMAL', () => {
      expect(getPrioridadeColor('NORMAL')).toBe('blue');
    });

    it('should return orange for ALTA', () => {
      expect(getPrioridadeColor('ALTA')).toBe('orange');
    });

    it('should return red for URGENTE', () => {
      expect(getPrioridadeColor('URGENTE')).toBe('red');
    });
  });

  describe('getClienteNome', () => {
    it('should return nome for PF cliente', () => {
      const cliente: ClienteResumo = {
        id: 1,
        tipo: 'PF',
        nome: 'João Silva',
      };
      expect(getClienteNome(cliente)).toBe('João Silva');
    });

    it('should return nome_fantasia for PJ cliente', () => {
      const cliente: ClienteResumo = {
        id: 1,
        tipo: 'PJ',
        razao_social: 'Empresa LTDA',
        nome_fantasia: 'Empresa',
      };
      expect(getClienteNome(cliente)).toBe('Empresa');
    });

    it('should return razao_social when nome_fantasia is missing', () => {
      const cliente: ClienteResumo = {
        id: 1,
        tipo: 'PJ',
        razao_social: 'Empresa LTDA',
      };
      expect(getClienteNome(cliente)).toBe('Empresa LTDA');
    });

    it('should return "-" when cliente is undefined', () => {
      expect(getClienteNome(undefined)).toBe('-');
    });

    it('should return "-" when nome is missing for PF', () => {
      const cliente: ClienteResumo = {
        id: 1,
        tipo: 'PF',
      };
      expect(getClienteNome(cliente)).toBe('-');
    });
  });

  describe('formatOSNumber', () => {
    it('should extract number from full OS format', () => {
      expect(formatOSNumber('OS-2024-0001')).toBe('0001');
    });

    it('should return original if not in expected format', () => {
      expect(formatOSNumber('123')).toBe('123');
    });

    it('should return empty string for empty input', () => {
      expect(formatOSNumber('')).toBe('');
    });
  });

  describe('formatDataEntrada', () => {
    it('should format date string to pt-BR format', () => {
      const result = formatDataEntrada('2024-01-15T10:00:00Z');
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    });

    it('should format Date object', () => {
      const date = new Date('2024-01-15T10:00:00Z');
      const result = formatDataEntrada(date);
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    });

    it('should return "-" for undefined', () => {
      expect(formatDataEntrada(undefined)).toBe('-');
    });
  });

  describe('formatDataPrevisao', () => {
    it('should format date string to pt-BR format', () => {
      const result = formatDataPrevisao('2024-01-20T10:00:00Z');
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    });

    it('should return "Não definida" for undefined', () => {
      expect(formatDataPrevisao(undefined)).toBe('Não definida');
    });
  });
});
