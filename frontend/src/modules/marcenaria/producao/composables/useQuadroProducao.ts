/**
 * @fileoverview O quadro da fábrica (Spec 12B D15-D18): todas as OS abertas
 * da marcenaria com o progresso, na ordem da previsão (a API já ordena).
 * Recarrega a cada 30 s: é um quadro de parede (D18).
 */
import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { REFETCH_DASHBOARD } from '@/core/config/queryIntervals';

import { getQuadro } from '../services/producao.service';
import { CHAVE_QUADRO } from './useProducaoDaOS';

export function useQuadroProducao(ativo: Ref<boolean>) {
  return useQuery({
    queryKey: CHAVE_QUADRO,
    queryFn: getQuadro,
    enabled: computed(() => ativo.value),
    refetchInterval: REFETCH_DASHBOARD,
  });
}
