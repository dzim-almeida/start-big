import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { DocumentoFiscalRead, EmissaoDevolucaoPayload } from '../types/fiscal.types';

export function useFiscalDevolucaoMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      documentoId,
      payload,
    }: {
      documentoId: number;
      payload: EmissaoDevolucaoPayload;
    }) => fiscalService.emitirDevolucao(documentoId, payload),
    onSuccess: (novo: DocumentoFiscalRead, { documentoId }) => {
      // A NF-e é assíncrona na SEFAZ: PROCESSANDO é normal, não é falha.
      if (novo.status === 'AUTORIZADA') {
        toast.success(`NF-e de devolução nº ${novo.numero_documento} autorizada.`);
      } else if (novo.status === 'PROCESSANDO') {
        toast.info(
          'NF-e de devolução enviada',
          'Aguardando a resposta da SEFAZ. Acompanhe no Centro Fiscal.',
        );
      } else {
        toast.warning(
          `NF-e de devolução ${novo.status.toLowerCase()}`,
          novo.mensagem_sefaz ?? 'Consulte o Centro Fiscal.',
        );
      }

      queryClient.invalidateQueries({ queryKey: fiscalKeys.documentos() });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.resumo() });
      // A origem ganhou saldo devolvido: quem estiver com ela aberta precisa ver.
      queryClient.invalidateQueries({ queryKey: fiscalKeys.documento(documentoId) });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.historico(documentoId) });
    },
    onError: (error) => {
      toast.error('A devolução não foi emitida', getErrorMessage(error as AxiosError<ApiError>));
    },
  });
}
