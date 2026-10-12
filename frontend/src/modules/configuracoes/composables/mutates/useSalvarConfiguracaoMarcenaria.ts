import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ConfiguracaoMarcenariaUpdate } from '../../schemas/configuracaoMarcenaria.schema';
import { updateConfiguracaoMarcenaria } from '../../services/configuracaoMarcenaria.service';
import { CONFIGURACAO_MARCENARIA_KEY } from '../queries/useConfiguracaoMarcenariaQuery';

/** Salva os parâmetros da marcenaria e atualiza a tela (Spec 04B §6.7). */
export function useSalvarConfiguracaoMarcenaria() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation<void, AxiosError<ApiError>, ConfiguracaoMarcenariaUpdate>({
    mutationFn: async (data) => {
      await updateConfiguracaoMarcenaria(data);
    },
    onSuccess: () => {
      toast.success('Parâmetros da marcenaria salvos com sucesso!');
      queryClient.invalidateQueries({ queryKey: [CONFIGURACAO_MARCENARIA_KEY] });   // relê da API
    },
    onError: (erro) => {
      // 422 traz a mensagem do backend (ex.: "O markup deve ficar entre 0% e 1000%.").
      toast.error(getErrorMessage(erro, 'Erro ao salvar os parâmetros. Tente novamente.'));
    },
  });
}
