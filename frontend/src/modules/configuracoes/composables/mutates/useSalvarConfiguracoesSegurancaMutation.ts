import { useMutation } from '@tanstack/vue-query'
import { AxiosError } from 'axios'
import { useToast } from '@/shared/composables/useToast'
import { updateConfiguracoesSeguranca } from '../../services/configuracoes.service'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'
import type { ConfiguracaoSegurancaRead, ConfiguracaoSegurancaUpdate } from '../../schemas/configuracoes.schema'
import type { ApiError } from '@/shared/types/axios.types'

export function useSalvarConfiguracoesSegurancaMutation() {
  const toast = useToast()
  const configuracoesStore = useConfiguracoesStore()

  return useMutation<ConfiguracaoSegurancaRead, AxiosError<ApiError>, ConfiguracaoSegurancaUpdate>({
    mutationFn: (data) => updateConfiguracoesSeguranca(data),
    onSuccess: (data) => {
      configuracoesStore.configSeguranca = data
      toast.success('Configurações de segurança salvas com sucesso!')
      configuracoesStore.carregarConfiguracoes()
    },
    onError: () => {
      toast.error('Erro ao salvar as configurações. Tente novamente.')
    },
  })
}
