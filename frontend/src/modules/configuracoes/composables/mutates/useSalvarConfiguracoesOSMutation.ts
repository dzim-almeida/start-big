import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { AxiosError } from 'axios'
import { useToast } from '@/shared/composables/useToast'
import { updateConfiguracoesOS } from '../../services/configuracoes.service'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import type { ConfiguracaoOSUpdate } from '../../schemas/configuracoes.schema'
import type { ApiError } from '@/shared/types/axios.types'

export function useSalvarConfiguracoesOSMutation() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const configuracoesStore = useConfiguracoesStore()

  return useMutation<void, AxiosError<ApiError>, ConfiguracaoOSUpdate>({
    mutationFn: async (data) => {
      await updateConfiguracoesOS(data)
    },
    onSuccess: () => {
      toast.success('Configurações de OS salvas com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['configuracoes-os'] })
      configuracoesStore.carregarConfiguracoes()
    },
    onError: () => {
      toast.error('Erro ao salvar as configurações. Tente novamente.')
    },
  })
}
