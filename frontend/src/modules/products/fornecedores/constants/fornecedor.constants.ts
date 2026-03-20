import type { StatusFilter } from '../types/fornecedor.types';

export const FORNECEDORES_QUERY_KEY = 'fornecedores';
export const FORNECEDORES_STALE_TIME = 1000 * 60 * 5;

export const STATUS_FILTER_CONFIG: Record<
  StatusFilter,
  { label: string; class: string; color: string }
> = {
  ativos: {
    label: 'Ativos',
    class: 'bg-emerald-50 text-emerald-600',
    color: 'bg-emerald-500',
  },
  inativos: {
    label: 'Inativos',
    class: 'bg-red-50 text-red-600',
    color: 'bg-red-500',
  },
};
