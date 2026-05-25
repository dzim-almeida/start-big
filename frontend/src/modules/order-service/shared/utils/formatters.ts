import type { OsStatusEnumDataType, OsPriorityEnumDataType } from '../../ordens/schemas/enums/osEnums.schema';
import type { CustomerUnionReadSchemaDataType } from '../../ordens/schemas/relationship/customer/customer.schema';
import { OS_STATUS_OPTIONS, OS_PRIORIDADE_OPTIONS } from '../../ordens/constants/ordemServico.constants';

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

export function getClienteNome(cliente?: CustomerUnionReadSchemaDataType): string {
  if (!cliente) return '-';
  const c = cliente as { tipo: string; nome?: string; nome_fantasia?: string; razao_social?: string };
  if (c.tipo === 'PF') return c.nome || '-';
  return c.nome_fantasia || c.razao_social || '-';
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

export function inferPaymentType(nome: string): string {
  const lower = nome.toLowerCase();
  if (lower.includes('pix')) return 'PIX';
  if (lower.includes('crédito') || lower.includes('credito')) return 'CARTAO_CREDITO';
  if (lower.includes('débito') || lower.includes('debito')) return 'CARTAO_DEBITO';
  if (lower.includes('boleto')) return 'BOLETO';
  if (lower.includes('transferência') || lower.includes('transferencia')) return 'TRANSFERENCIA';
  if (lower.includes('dinheiro')) return 'DINHEIRO';
  return 'OUTROS';
}

export function inferPermiteParcelamento(tipo: string): boolean {
  return tipo === 'CARTAO_CREDITO';
}

export function getPaymentDisplayName(nome: string): string {
  const map: Record<string, string> = {
    'PIX': 'Pix',
    'DINHEIRO': 'Dinheiro',
    'CARTAO_CREDITO': 'Cartao de Credito',
    'CARTAO_DEBITO': 'Cartao de Debito',
    'BOLETO': 'Boleto',
    'TRANSFERENCIA': 'Transferencia',
  };
  return map[nome.toUpperCase()] ?? nome;
}
