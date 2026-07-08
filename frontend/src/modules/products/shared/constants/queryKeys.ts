import { REFETCH_CADASTROS } from '@/core/config/queryIntervals';

export const PRODUTOS_QUERY_KEY = 'produtos';
export const PRODUTOS_STALE_TIME = 1000 * 60 * 5;
export const PRODUTOS_REFETCH_INTERVAL = REFETCH_CADASTROS;

export const FORNECEDORES_QUERY_KEY = 'fornecedores';
export const FORNECEDORES_STALE_TIME = 1000 * 60 * 5;
export const FORNECEDORES_REFETCH_INTERVAL = REFETCH_CADASTROS;