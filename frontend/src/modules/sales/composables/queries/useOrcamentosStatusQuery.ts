import { useQuery } from '@tanstack/vue-query';

import { orcamentoService } from '../../orcamento.service';
import { orcamentoKeys } from '../../query.keys';

import { OrcamentosStatus } from '../../schemas/orcamento.schema';

export function useOrcamentosStatusQuery() {
  return useQuery<OrcamentosStatus>({
    queryKey: orcamentoKeys.status(),
    queryFn: () => orcamentoService.getOrcamentosStatus(),
    staleTime: 1000 * 60 * 30,
  });
}
