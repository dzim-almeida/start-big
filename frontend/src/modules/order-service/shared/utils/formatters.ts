import type { OsStatusEnumDataType, OsPriorityEnumDataType } from '../../ordens/schemas/enums/osEnums.schema';
import { OS_STATUS_OPTIONS, OS_PRIORIDADE_OPTIONS } from '../../ordens/constants/ordemServico.constants';

// Re-export shared utilities for backward compatibility
export { getClienteNome, getPaymentDisplayName, inferPaymentType, inferPermiteParcelamento } from '@/shared/utils/print.utils';

export function getStatusLabel(status: OsStatusEnumDataType): string {
  const found = OS_STATUS_OPTIONS.find((s) => s.value === status);
  return found?.label || status;
}

export function getStatusColor(status: OsStatusEnumDataType): string {
  const found = OS_STATUS_OPTIONS.find((s) => s.value === status);
  return found?.color || 'gray';
}

export function getPrioridadeLabel(prioridade: OsPriorityEnumDataType): string {
  const found = OS_PRIORIDADE_OPTIONS.find((p) => p.value === prioridade);
  return found?.label || prioridade;
}

export function getPrioridadeColor(prioridade: OsPriorityEnumDataType): string {
  const found = OS_PRIORIDADE_OPTIONS.find((p) => p.value === prioridade);
  return found?.color || 'gray';
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
