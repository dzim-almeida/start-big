import { useMutation, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { InutilizacaoRead, InutilizacaoRequest } from '../types/fiscal.types';

export type DesfechoInutilizacao =
  | { tipo: 'sucesso'; titulo: string; descricao?: string }
  | { tipo: 'aguardando'; titulo: string; descricao: string }
  | { tipo: 'rejeitada'; titulo: string; descricao: string }
  | { tipo: 'nao_transmitida'; titulo: string; descricao: string }
  | { tipo: 'incerta'; titulo: string; descricao: string };

function faixa(i: Pick<InutilizacaoRead, 'serie' | 'numero_inicial' | 'numero_final'>): string {
  return i.numero_inicial === i.numero_final
    ? `nº ${i.numero_inicial} (série ${i.serie})`
    : `nº ${i.numero_inicial} a ${i.numero_final} (série ${i.serie})`;
}

/**
 * O que dizer ao operador para cada resposta. Puro, para ser testável.
 *
 * Cinco desfechos, e os três "não" são diferentes entre si — o que muda é
 * PARA ONDE mandar o lojista olhar:
 *
 *   REJEITADA        a SEFAZ recusou, com código → a mensagem dela é a ação
 *   NAO_TRANSMITIDA  a plataforma recusou ANTES da SEFAZ → olhar a configuração
 *                    da licença, não a SEFAZ; a faixa continua aberta
 *   INDETERMINADA    sem resposta → NÃO refazer o pedido: pode ter registrado
 *
 * Todos chegam com HTTP 200: não são falhas do sistema, e o toast não é de erro.
 */
export function resolverDesfechoInutilizacao(i: InutilizacaoRead): DesfechoInutilizacao {
  switch (i.status) {
    case 'HOMOLOGADA':
      return {
        tipo: 'sucesso',
        titulo: `Faixa ${faixa(i)} inutilizada na SEFAZ.`,
        descricao: i.protocolo ? `Protocolo ${i.protocolo}.` : undefined,
      };
    case 'PROCESSANDO':
    case 'PENDENTE':
      return {
        tipo: 'aguardando',
        titulo: 'A SEFAZ ainda não respondeu',
        descricao: 'O pedido foi enviado. Consulte de novo em instantes.',
      };
    case 'REJEITADA':
      return {
        tipo: 'rejeitada',
        titulo: 'A SEFAZ recusou a inutilização',
        descricao: i.mensagem_sefaz ?? 'Consulte o Centro Fiscal.',
      };
    case 'NAO_TRANSMITIDA':
      return {
        tipo: 'nao_transmitida',
        titulo: 'O pedido não chegou à SEFAZ',
        descricao:
          (i.mensagem_sefaz ?? 'A plataforma de emissão recusou antes de transmitir.') +
          ' A faixa continua aberta — confira a configuração fiscal e tente de novo.',
      };
    default:
      return {
        tipo: 'incerta',
        titulo: 'Não foi possível confirmar com a SEFAZ',
        descricao:
          (i.mensagem_sefaz ?? 'A resposta não chegou.') +
          ' Não peça de novo: a faixa pode já ter sido registrada. Consulte o histórico.',
      };
  }
}

export function useFiscalInutilizarMutation() {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InutilizacaoRequest) => fiscalService.inutilizarNumeracao(payload),
    onSuccess: (registro) => {
      const d = resolverDesfechoInutilizacao(registro);
      if (d.tipo === 'sucesso') toast.success(d.titulo, d.descricao);
      else if (d.tipo === 'aguardando') toast.info(d.titulo, d.descricao);
      else if (d.tipo === 'rejeitada' || d.tipo === 'nao_transmitida') toast.warning(d.titulo, d.descricao);
      else toast.error(d.titulo, d.descricao);

      // A faixa sai (ou volta) da lista de buracos conforme o desfecho, e o
      // histórico ganha a linha. Os dois precisam perguntar de novo.
      queryClient.invalidateQueries({ queryKey: fiscalKeys.numeracaoGaps() });
      queryClient.invalidateQueries({ queryKey: fiscalKeys.inutilizacoes() });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error as AxiosError<ApiError>));
    },
  });
}
