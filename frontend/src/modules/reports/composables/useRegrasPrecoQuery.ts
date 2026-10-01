import { type MaybeRef, unref, computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { getRegrasPreco } from '../report.service';
import { reportKeys } from '../query.keys';

export function useRegrasPrecoQuery(inicio: MaybeRef<string>, fim: MaybeRef<string>) {
  return useQuery({
    queryKey: computed(() => reportKeys.regrasPreco(unref(inicio), unref(fim))),
    queryFn: () => getRegrasPreco(unref(inicio), unref(fim)),
    enabled: computed(() => !!unref(inicio) && !!unref(fim)),
    staleTime: 1000 * 60,
  });
}
