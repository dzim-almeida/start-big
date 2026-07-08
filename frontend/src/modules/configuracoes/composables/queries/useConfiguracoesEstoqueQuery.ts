import { useQuery } from '@tanstack/vue-query'
import { getConfiguracoesProdutos } from '../../services/configuracoes.service'
import { REFETCH_CONFIG } from '@/core/config/queryIntervals'

export const CONFIGURACOES_PRODUTOS_KEY = 'configuracoes-produtos'

export function useConfiguracoesEstoqueQuery() {
  return useQuery({
    queryKey: [CONFIGURACOES_PRODUTOS_KEY],
    queryFn: getConfiguracoesProdutos,
    staleTime: REFETCH_CONFIG,
    refetchInterval: REFETCH_CONFIG,
  })
}
