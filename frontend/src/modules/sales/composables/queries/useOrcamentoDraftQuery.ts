import { type MaybeRef, unref, computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { orcamentoService } from '../../orcamento.service';
import { orcamentoKeys } from '../../query.keys';

import { OrcamentoRead } from '../../schemas/orcamento.schema';

export function useOrcamentoDraftQuery(orcamentoId: MaybeRef<number | null | undefined>) {
  return useQuery<OrcamentoRead>({
    queryKey: computed(() =>
      !!unref(orcamentoId)
        ? orcamentoKeys.draft(unref(orcamentoId)!)
        : ([...orcamentoKeys.all, 'draft', 'empty'] as const),
    ),

    queryFn: () => orcamentoService.getOrcamento(unref(orcamentoId)!),
    enabled: computed(() => !!unref(orcamentoId)),
    staleTime: 1000 * 15,
  });
}
