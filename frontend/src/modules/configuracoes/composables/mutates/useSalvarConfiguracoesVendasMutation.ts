import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { AxiosError } from 'axios'
import { useToast } from '@/shared/composables/useToast'
import { updateConfiguracoesVendas } from '../../services/configuracoes.service'
import { CONFIGURACOES_VENDAS_KEY } from '../queries/useConfiguracoesVendasQuery'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import type { ConfiguracaoVendasUpdate } from '../../schemas/configuracoes.schema'
import type { ApiError } from '@/shared/types/axios.types'

export function useSalvarConfiguracoesVendasMutation() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const configuracoesStore = useConfiguracoesStore()

  return useMutation<void, AxiosError<ApiError>, ConfiguracaoVendasUpdate>({
    mutationFn: async (data) => {
      await updateConfiguracoesVendas(data)
    },
    onSuccess: () => {
      toast.success('Configurações de vendas salvas com sucesso!')
      queryClient.invalidateQueries({ queryKey: [CONFIGURACOES_VENDAS_KEY] })
      configuracoesStore.carregarConfiguracoes()
    },
    onError: () => {
      toast.error('Erro ao salvar as configurações. Tente novamente.')
    },
  })
}
