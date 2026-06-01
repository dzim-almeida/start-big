import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { AxiosError } from 'axios'
import { useToast } from '@/shared/composables/useToast'
import { updateConfiguracoesClientes } from '../../services/configuracoes.service'
import { CONFIGURACOES_CLIENTES_KEY } from '../queries/useConfiguracoesClientesQuery'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import type { ConfiguracaoClientesUpdate } from '../../schemas/configuracoes.schema'
import type { ApiError } from '@/shared/types/axios.types'

export function useSalvarConfiguracoesClientesMutation() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const configuracoesStore = useConfiguracoesStore()

  return useMutation<void, AxiosError<ApiError>, ConfiguracaoClientesUpdate>({
    mutationFn: async (data) => {
      await updateConfiguracoesClientes(data)
    },
    onSuccess: () => {
      toast.success('Configurações de clientes salvas com sucesso!')
      queryClient.invalidateQueries({ queryKey: [CONFIGURACOES_CLIENTES_KEY] })
      configuracoesStore.carregarConfiguracoes()
    },
    onError: () => {
      toast.error('Erro ao salvar as configurações. Tente novamente.')
    },
  })
}
