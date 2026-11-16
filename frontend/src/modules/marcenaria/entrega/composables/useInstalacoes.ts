/**
 * @fileoverview A lista de instalações (aba "Instalações" em Serviços, Spec
 * 13B D15-D17): quem instala onde, no período escolhido.
 *
 * O período e o "Só atrasadas" vão para a API; o montador é filtrado AQUI,
 * sobre a lista do período: assim o filtro mostra os montadores do período
 * sem buscar o cadastro de funcionários (que pede outra permissão).
 */
import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { REFETCH_DASHBOARD } from '@/core/config/queryIntervals';

import { getInstalacoes } from '../services/agenda.service';
import { CHAVE_INSTALACOES } from './useEntregaDaOS';

export function useInstalacoes(filtros: Ref<{ de: string | null; ate: string | null; atrasadas: boolean }>) {
  return useQuery({
    queryKey: computed(() => [...CHAVE_INSTALACOES, filtros.value]),
    queryFn: () => getInstalacoes(filtros.value),
    refetchInterval: REFETCH_DASHBOARD,              // outro computador pode ter registrado uma entrega
  });
}
