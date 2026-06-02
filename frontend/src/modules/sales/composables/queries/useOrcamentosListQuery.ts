import { type MaybeRef, unref, computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { OrcamentoList, OrcamentoSearch } from '../../schemas/orcamento.schema';
import { orcamentoKeys } from '../../query.keys';
import { orcamentoService } from '../../orcamento.service';

export function useOrcamentosListQuery(
  filters?: MaybeRef<OrcamentoSearch | null | undefined>,
  page?: MaybeRef<number | null | undefined>,
) {
  return useQuery<OrcamentoList>({
    queryKey: computed(() =>
      !!unref(filters)
        ? orcamentoKeys.list(unref(filters) ?? undefined, unref(page) ?? 1)
        : orcamentoKeys.list(undefined, unref(page) ?? 1)
    ),
    queryFn: () => orcamentoService.listOrcamentos(unref(filters)!, unref(page)!),
    staleTime: 1000 * 30,
  });
}
