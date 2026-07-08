import { useQuery } from '@tanstack/vue-query'
import { getConfiguracoesClientes } from '../../services/configuracoes.service'
import { REFETCH_CONFIG } from '@/core/config/queryIntervals'

export const CONFIGURACOES_CLIENTES_KEY = 'configuracoes-clientes'

export function useConfiguracoesClientesQuery() {
  return useQuery({
    queryKey: [CONFIGURACOES_CLIENTES_KEY],
    queryFn: getConfiguracoesClientes,
    staleTime: REFETCH_CONFIG,
    refetchInterval: REFETCH_CONFIG,
  })
}
