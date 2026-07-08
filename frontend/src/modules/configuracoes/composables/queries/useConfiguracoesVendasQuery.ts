import { useQuery } from '@tanstack/vue-query'
import { getConfiguracoesVendas } from '../../services/configuracoes.service'
import { REFETCH_CONFIG } from '@/core/config/queryIntervals'

export const CONFIGURACOES_VENDAS_KEY = 'configuracoes-vendas'

export function useConfiguracoesVendasQuery() {
  return useQuery({
    queryKey: [CONFIGURACOES_VENDAS_KEY],
    queryFn: getConfiguracoesVendas,
    staleTime: REFETCH_CONFIG,
    refetchInterval: REFETCH_CONFIG,
  })
}
