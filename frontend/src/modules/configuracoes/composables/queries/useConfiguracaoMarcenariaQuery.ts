import { useQuery } from '@tanstack/vue-query';

import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { getConfiguracaoMarcenaria } from '../../services/configuracaoMarcenaria.service';

export const CONFIGURACAO_MARCENARIA_KEY = 'configuracao-marcenaria';

/**
 * Parâmetros da marcenaria (Spec 04B, D6). Query própria, e não o store global
 * de configurações: o store carrega no boot para TODOS os segmentos, e esta
 * rota responde 404 fora da marcenaria. Com `enabled`, os outros segmentos
 * nem fazem a chamada.
 */
export function useConfiguracaoMarcenariaQuery() {
  const { temOrcamentoTecnico } = useCapacidades();
  return useQuery({
    queryKey: [CONFIGURACAO_MARCENARIA_KEY],
    queryFn: getConfiguracaoMarcenaria,
    enabled: temOrcamentoTecnico,          // só no segmento com orçamento técnico
  });
}
