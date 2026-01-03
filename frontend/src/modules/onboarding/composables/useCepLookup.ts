/**
 * @fileoverview Composable para busca de CEP
 * @description Encapsula a lógica de consulta de CEP usando a API ViaCEP
 * com debounce e tratamento de erros.
 */

import { computed, Ref } from 'vue';
import { getAddressByCep } from '../services/onboarding.service';
import { useQuery } from '@tanstack/vue-query';
import { unmaskCep } from '@/shared/utils/unmask.utils';

/**
 * Composable para busca automática de endereço por CEP
 * @returns Objeto com estados e métodos para consulta de CEP
 */

export function useCepQuery(cep: Ref<string>) {
  const cleanCep = computed(() => unmaskCep(cep.value))

  return useQuery({
    queryKey: ['cep', cleanCep],
    queryFn: () => getAddressByCep(cleanCep.value),
    enabled: computed(() => cleanCep.value.length === 8),
    staleTime: 1000 * 60 * 60, // 1 hora
    retry: 2,
  });
}
