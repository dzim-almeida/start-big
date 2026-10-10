/**
 * @fileoverview O resumo da entrega para o aviso da finalização (Spec 13B D18).
 * Só existe dentro do `AvisoEntregaFinalizacao`, que só é montado na
 * marcenaria (D19): os outros segmentos nunca chamam `/marcenaria/...`.
 */
import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { getResumo } from '../services/entrega.service';
import { chaveResumo } from './useEntregaDaOS';

export function useResumoEntrega(numeroOs: Ref<string>) {
  return useQuery({
    queryKey: computed(() => chaveResumo(numeroOs.value)),
    queryFn: () => getResumo(numeroOs.value),
    enabled: computed(() => !!numeroOs.value),
    retry: false,                                    // OS sem orçamento (404): o aviso só não aparece
    staleTime: 0,                                    // a finalização sempre confere o que vale agora
  });
}
