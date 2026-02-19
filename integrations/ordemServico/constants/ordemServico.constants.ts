import type { OrdemServicoStatus, OrdemServicoPrioridade } from '../types/ordemServico.types';

export const OS_STATUS_OPTIONS = [
  { value: 'ABERTA' as OrdemServicoStatus, label: 'Aberta', color: 'blue' },
  { value: 'EM_ANDAMENTO' as OrdemServicoStatus, label: 'Em Andamento', color: 'yellow' },
  { value: 'AGUARDANDO_PECAS' as OrdemServicoStatus, label: 'Aguardando Peças', color: 'orange' },
  { value: 'AGUARDANDO_APROVACAO' as OrdemServicoStatus, label: 'Aguardando Aprovação', color: 'yellow' },
  { value: 'AGUARDANDO_RETIRADA' as OrdemServicoStatus, label: 'Aguardando Retirada', color: 'indigo' },
  { value: 'FINALIZADA' as OrdemServicoStatus, label: 'Finalizada', color: 'green' },
  { value: 'CANCELADA' as OrdemServicoStatus, label: 'Cancelada', color: 'red' },
] as const;

export const OS_PRIORIDADE_OPTIONS = [
  { value: 'BAIXA' as OrdemServicoPrioridade, label: 'Baixa', color: 'gray' },
  { value: 'NORMAL' as OrdemServicoPrioridade, label: 'Normal', color: 'blue' },
  { value: 'ALTA' as OrdemServicoPrioridade, label: 'Alta', color: 'orange' },
  { value: 'URGENTE' as OrdemServicoPrioridade, label: 'Urgente', color: 'red' },
] as const;

export const DEFAULT_OS_STATUS: OrdemServicoStatus = 'ABERTA';
export const DEFAULT_OS_PRIORIDADE: OrdemServicoPrioridade = 'NORMAL';
export const DEFAULT_GARANTIA_DIAS = 90;

export const OS_BASE_URL = '/ordens-servico';
export const OS_FOTOS_URL = '/ordens-servico-fotos';

export const OS_ITEMS_PER_PAGE = 10;
export const SERVICE_ITEMS_PER_PAGE = 10;

export const OS_STALE_TIME = 1000 * 60 * 2;
export const OS_LIST_STALE_TIME = 1000 * 60 * 2;
export const OS_STATS_STALE_TIME = 1000 * 60 * 5;
export const SERVICE_STALE_TIME = 1000 * 60 * 2;
export const SERVICE_STATS_STALE_TIME = 1000 * 60 * 5;

export const SEARCH_DEBOUNCE_MS = 300;

export const STORAGE_KEY_OS_FILTER = 'os_filter_status';

export const EQUIPMENT_HISTORY_LIMIT = 20;

export const REOPEN_MODES = {
  NONE: 'NONE',
  TEXT_ONLY: 'TEXT_ONLY',
  FULL: 'FULL',
} as const;

export type ReopenMode = typeof REOPEN_MODES[keyof typeof REOPEN_MODES];
