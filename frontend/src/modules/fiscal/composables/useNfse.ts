import { computed } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { nfseService } from '../services/nfse.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { EmissaoResponse } from '../types/fiscal.types';

/**
 * A aba NFS-e: a lista e as três ações (emitir, consultar, cancelar).
 *
 * A lista se atualiza sozinha enquanto houver nota em PROCESSANDO: o backend
 * já consulta em segundo plano (o mesmo polling da NF-e), e sem isto a tela só
 * mostraria a autorização depois de alguém recarregar.
 */
export function useNfseDocumentosQuery() {
  const query = useQuery({
    queryKey: fiscalKeys.nfseDocumentos(),
    queryFn: () => nfseService.listarDocumentos(),
    refetchInterval: (q) =>
      (q.state.data ?? []).some((d) => d.status === 'PROCESSANDO') ? 5_000 : false,
  });
  const documentos = computed(() => query.data.value ?? []);
  return { ...query, documentos };
}

/** Toast pelo desfecho: autorizada não é igual a rejeitada nem a "sem retorno". */
function avisarDesfecho(toast: ReturnType<typeof useToast>, r: EmissaoResponse) {
  if (r.status === 'AUTORIZADA') toast.success('NFS-e autorizada.');
  else if (r.status === 'PROCESSANDO') toast.info('NFS-e enviada. A autorização aparece aqui em instantes.');
  else if (r.status === 'CANCELADA') toast.success('NFS-e cancelada.');
  else toast.error(r.mensagem || `NFS-e ${r.status.toLowerCase()}.`);
}

/** O 409 da plataforma para nota igual a outra autorizada há menos de 1 h. */
export const CODIGO_NOTA_REPETIDA = 'NOTA_DUPLICADA_SUSPEITA';

export function codigoDoErro(error: unknown): string | undefined {
  return (error as AxiosError<{ detail?: { codigo?: string } }>)?.response?.data?.detail?.codigo;
}

function useNfseMutation<T>(fn: (v: T) => Promise<EmissaoResponse>) {
  const toast = useToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: (r) => {
      avisarDesfecho(toast, r);
      queryClient.invalidateQueries({ queryKey: fiscalKeys.nfseDocumentos() });
    },
    onError: (error) => {
      // A nota repetida não é erro para toast: o modal pergunta ao operador.
      if (codigoDoErro(error) === CODIGO_NOTA_REPETIDA) return;
      toast.error(getErrorMessage(error as AxiosError<ApiError>));
    },
  });
}

export const useNfseEmitirMutation = () =>
  useNfseMutation(({ numeroOs, confirmar = false }: { numeroOs: string; confirmar?: boolean }) =>
    nfseService.emitirOs(numeroOs, confirmar),
  );

export const useNfseConsultarMutation = () => useNfseMutation((id: number) => nfseService.consultar(id));

export const useNfseCancelarMutation = () =>
  useNfseMutation(({ id, justificativa }: { id: number; justificativa: string }) =>
    nfseService.cancelar(id, justificativa),
  );
