import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { CartaCorrecaoRead } from '../types/fiscal.types';

export type DesfechoCarta =
  | { tipo: 'sucesso'; titulo: string; descricao?: string }
  | { tipo: 'rejeitada'; titulo: string; descricao: string }
  | { tipo: 'erro'; titulo: string; descricao: string };

/**
 * O que dizer ao operador para cada resposta. Puro, para ser testável.
 *
 * REJEITADA chega com HTTP 200: a SEFAZ é quem recusou, e a mensagem dela é
 * o que diz o que fazer -- não é falha do sistema, e o toast é de aviso.
 */
export function resolverDesfechoCarta(carta: CartaCorrecaoRead): DesfechoCarta {
  if (carta.status === 'AUTORIZADA') {
    return {
      tipo: 'sucesso',
      titulo: `Carta de correção nº ${carta.sequencia ?? '?'} registrada na SEFAZ.`,
    };
  }
  if (carta.status === 'REJEITADA') {
    return {
      tipo: 'rejeitada',
      titulo: 'A SEFAZ recusou a carta de correção',
      descricao: carta.mensagem_sefaz ?? 'Consulte o Centro Fiscal.',
    };
  }
  return {
    tipo: 'erro',
    titulo: 'A carta de correção não foi registrada',
    descricao: carta.mensagem_sefaz ?? 'A emissora não aceitou o envio. Tente de novo.',
  };
}

export function useFiscalCartaCorrecaoMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, correcao }: { id: number; correcao: string }) =>
      fiscalService.emitirCartaCorrecao(id, correcao),
    onSuccess: (carta) => {
      const desfecho = resolverDesfechoCarta(carta);
      if (desfecho.tipo === 'sucesso') toast.success(desfecho.titulo, desfecho.descricao);
      else if (desfecho.tipo === 'rejeitada') toast.warning(desfecho.titulo, desfecho.descricao);
      else toast.error(desfecho.titulo, desfecho.descricao);

      // O documento ganha `total_cartas_correcao`/`ultima_carta_correcao`; a
      // lista mostra o selo. `resumo()` fica de fora: os contadores por
      // status não mudam -- a nota continua autorizada.
      queryClient.invalidateQueries({ queryKey: fiscalKeys.cartasCorrecao(carta.documento_id) });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.documento(carta.documento_id) });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.documentos() });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error as AxiosError<ApiError>));
    },
  });
}
