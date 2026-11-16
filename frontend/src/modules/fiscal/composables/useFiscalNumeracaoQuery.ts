import { useQuery } from '@tanstack/vue-query';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys, FISCAL_STALE_TIME } from '../constants/fiscal.constants';

/** Faixas reservadas que nunca viraram nota. Cada uma é um pedido à SEFAZ pendente. */
export function useFiscalGapsNumeracaoQuery() {
  return useQuery({
    queryKey: fiscalKeys.numeracaoGaps(),
    queryFn: () => fiscalService.listarGapsNumeracao(),
    staleTime: FISCAL_STALE_TIME,
  });
}

/** Histórico de inutilizações — o que já foi pedido, e como a SEFAZ respondeu. */
export function useFiscalInutilizacoesQuery() {
  return useQuery({
    queryKey: fiscalKeys.inutilizacoes(),
    queryFn: () => fiscalService.listarInutilizacoes(),
    staleTime: FISCAL_STALE_TIME,
  });
}
