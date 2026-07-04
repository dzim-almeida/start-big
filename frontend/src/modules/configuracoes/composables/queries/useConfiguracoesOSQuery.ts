import { useQuery } from '@tanstack/vue-query'
import { getConfiguracoesOS } from '../../services/configuracoes.service'
import { REFETCH_CONFIG } from '@/core/config/queryIntervals'

export const CONFIGURACOES_OS_KEY = 'configuracoes-os'

export function useConfiguracoesOSQuery() {
  return useQuery({
    queryKey: [CONFIGURACOES_OS_KEY],
    queryFn: getConfiguracoesOS,
    staleTime: REFETCH_CONFIG,
    refetchInterval: REFETCH_CONFIG,
  })
}
