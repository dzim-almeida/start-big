import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { EmissaoNFeRequest, FiscalConflictDetail } from '../types/fiscal.types';

export function useFiscalEmitirNfeMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: EmissaoNFeRequest) => fiscalService.emitirNfe(payload),
    onSuccess: (data) => {
      if (data.status === 'AUTORIZADA' || data.status === 'PROCESSANDO') {
        toast.success(data.mensagem || 'NF-e emitida com sucesso.');
      } else {
        toast.error(data.mensagem || 'Erro ao emitir NF-e.');
      }
      queryClient.invalidateQueries({ queryKey: fiscalKeys.documentos() });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.resumo() });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.franquia() });
    },
    onError: (error) => {
      const axiosErr = error as AxiosError<ApiError>;

      // Só o conflito de documento vem como objeto ({codigo, mensagem}). O
      // `_handle_db_transaction` também devolve 409 para QUALQUER ValueError
      // do montador da nota (ex.: CFOP 5xxx e 6xxx na mesma venda), com o
      // motivo em texto puro — esse cai no toast de erro abaixo, com o motivo.
      const detail = axiosErr.response?.data?.detail as FiscalConflictDetail | string | undefined;
      if (axiosErr.response?.status === 409 && detail && typeof detail === 'object') {
        const msg = detail.mensagem || 'Esta venda já possui documento fiscal ativo.';
        toast.warning('Documento fiscal existente', msg);
        queryClient.invalidateQueries({ queryKey: fiscalKeys.documentos() });
        queryClient.invalidateQueries({ queryKey: fiscalKeys.resumo() });
        queryClient.invalidateQueries({ queryKey: fiscalKeys.franquia() });
        return;
      }

      toast.error(getErrorMessage(axiosErr));
    },
  });
}
