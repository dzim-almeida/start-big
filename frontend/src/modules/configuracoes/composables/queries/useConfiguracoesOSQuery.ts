import { useQuery } from '@tanstack/vue-query'
import { getConfiguracoesOS } from '../../services/configuracoes.service'

export const CONFIGURACOES_OS_KEY = 'configuracoes-os'

export function useConfiguracoesOSQuery() {
  return useQuery({
    queryKey: [CONFIGURACOES_OS_KEY],
    queryFn: getConfiguracoesOS,
    staleTime: Infinity,
  })
}
