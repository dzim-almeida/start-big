/**
 * Chaves de cache do módulo de Compras.
 *
 * Todas pendem de `COMPRAS_KEY`, pelo mesmo motivo das do financeiro: o
 * TanStack casa chave por PREFIXO, e uma `invalidateQueries([COMPRAS_KEY])`
 * alcança tudo o que está aqui (ver shared/constants/entityKeys.ts).
 */
import { COMPRAS_KEY } from '@/shared/constants/entityKeys';

export const comprasKeys = {
  todos: [COMPRAS_KEY] as const,
  fornecedores: () => [COMPRAS_KEY, 'fornecedores'] as const,
  fornecedoresDoProduto: (produtoId: number) => [COMPRAS_KEY, 'produto', produtoId, 'fornecedores'] as const,
  necessidades: () => [COMPRAS_KEY, 'necessidades'] as const,
  pedidos: (filtros?: unknown) => [COMPRAS_KEY, 'pedidos', filtros] as const,
  pedido: (id: number) => [COMPRAS_KEY, 'pedido', id] as const,
  buscaProduto: (termo: string) => [COMPRAS_KEY, 'busca-produto', termo] as const,
};
