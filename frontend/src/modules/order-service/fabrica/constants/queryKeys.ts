/**
 * Chaves de cache da marcenaria-fábrica. Todas pendem de `FABRICA_KEY` (o
 * TanStack casa por prefixo — ver shared/constants/entityKeys.ts).
 */
import { FABRICA_KEY } from '@/shared/constants/entityKeys';

export const fabricaKeys = {
  todos: [FABRICA_KEY] as const,
  insumo: (produtoId: number) => [FABRICA_KEY, 'produto', produtoId, 'insumo'] as const,
  buscaInsumo: (termo: string) => [FABRICA_KEY, 'busca-insumo', termo] as const,
  orcamentos: (numeroOs: string) => [FABRICA_KEY, 'os', numeroOs, 'orcamentos'] as const,
  orcamento: (id: number) => [FABRICA_KEY, 'orcamento', id] as const,
  trilho: (numeroOs: string) => [FABRICA_KEY, 'os', numeroOs, 'trilho'] as const,
};
