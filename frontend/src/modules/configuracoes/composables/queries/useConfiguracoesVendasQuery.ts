import { useQuery } from '@tanstack/vue-query'
import { getConfiguracoesVendas } from '../../services/configuracoes.service'

export const CONFIGURACOES_VENDAS_KEY = 'configuracoes-vendas'

export function useConfiguracoesVendasQuery() {
  return useQuery({
    queryKey: [CONFIGURACOES_VENDAS_KEY],
    queryFn: getConfiguracoesVendas,
    staleTime: Infinity,
  })
}
