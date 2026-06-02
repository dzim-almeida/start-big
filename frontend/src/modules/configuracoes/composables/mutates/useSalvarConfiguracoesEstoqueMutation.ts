import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { AxiosError } from 'axios'
import { useToast } from '@/shared/composables/useToast'
import { updateConfiguracoesProdutos } from '../../services/configuracoes.service'
import { CONFIGURACOES_PRODUTOS_KEY } from '../queries/useConfiguracoesEstoqueQuery'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import type { ConfiguracaoProdutosUpdate } from '../../schemas/configuracoes.schema'
import type { ApiError } from '@/shared/types/axios.types'

export function useSalvarConfiguracoesEstoqueMutation() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const configuracoesStore = useConfiguracoesStore()

  return useMutation<void, AxiosError<ApiError>, ConfiguracaoProdutosUpdate>({
    mutationFn: async (data) => {
      await updateConfiguracoesProdutos(data)
    },
    onSuccess: () => {
      toast.success('Configurações de produtos salvas com sucesso!')
      queryClient.invalidateQueries({ queryKey: [CONFIGURACOES_PRODUTOS_KEY] })
      configuracoesStore.carregarConfiguracoes()
    },
    onError: () => {
      toast.error('Erro ao salvar as configurações. Tente novamente.')
    },
  })
}
