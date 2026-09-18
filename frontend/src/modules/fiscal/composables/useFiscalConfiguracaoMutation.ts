import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { FiscalConfiguracaoUpdate } from '../types/fiscal.types';

export function useFiscalConfiguracaoMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: FiscalConfiguracaoUpdate) => fiscalService.atualizarConfiguracao(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fiscalKeys.configuracao() });
    },
  });
}
