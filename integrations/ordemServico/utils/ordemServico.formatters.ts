import type { OrdemServicoStatus, OrdemServicoPrioridade, ClienteResumo } from '../types/ordemServico.types';
import { OS_STATUS_OPTIONS, OS_PRIORIDADE_OPTIONS } from '../constants';

export function getStatusLabel(status: OrdemServicoStatus): string {
  const found = OS_STATUS_OPTIONS.find((s) => s.value === status);
  return found?.label || status;
}

export function getStatusColor(status: OrdemServicoStatus): string {
  const found = OS_STATUS_OPTIONS.find((s) => s.value === status);
  return found?.color || 'gray';
}

export function getPrioridadeLabel(prioridade: OrdemServicoPrioridade): string {
  const found = OS_PRIORIDADE_OPTIONS.find((p) => p.value === prioridade);
  return found?.label || prioridade;
}

export function getPrioridadeColor(prioridade: OrdemServicoPrioridade): string {
  const found = OS_PRIORIDADE_OPTIONS.find((p) => p.value === prioridade);
  return found?.color || 'gray';
}

export function getClienteNome(cliente?: ClienteResumo): string {
  if (!cliente) return '-';
  if (cliente.tipo === 'PF') return cliente.nome || '-';
  return cliente.nome_fantasia || cliente.razao_social || '-';
}

export function formatOSNumber(numero: string): string {
  if (!numero) return '';
  const parts = numero.split('-');
  return parts.length >= 3 ? parts[2] : numero;
}

export function formatDataEntrada(data: string | Date | undefined): string {
  if (!data) return '-';
  const date = typeof data === 'string' ? new Date(data) : data;
  return date.toLocaleDateString('pt-BR');
}

export function formatDataPrevisao(data: string | Date | undefined): string {
  if (!data) return 'Não definida';
  const date = typeof data === 'string' ? new Date(data) : data;
  return date.toLocaleDateString('pt-BR');
}
