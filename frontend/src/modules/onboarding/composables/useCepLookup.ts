/**
 * @fileoverview Composable para busca de CEP
 * @description Encapsula a lógica de consulta de CEP usando a API ViaCEP
 * com cache e tratamento de erros.
 */

import { computed, type Ref } from 'vue';
import { getAddressByCep } from '../services/onboarding.service';
import { useQuery } from '@tanstack/vue-query';
import { unmaskCep } from '@/shared/utils/unmask.utils';

/* ============================================
   Constants
   ============================================ */

/** Tempo de cache para consultas de CEP (1 hora em ms) */
const CEP_STALE_TIME = 1000 * 60 * 60;

/** Número de tentativas em caso de erro */
const CEP_RETRY_COUNT = 2;

/** Tamanho esperado do CEP sem máscara */
const CEP_LENGTH = 8;

/* ============================================
   Composable
   ============================================ */

/**
 * Composable para busca automática de endereço por CEP
 * @param {Ref<string>} cep - Ref reativa contendo o CEP digitado (com ou sem máscara)
 * @returns Query do TanStack com dados do endereço, estados de loading e erro
 */
export function useCepQuery(cep: Ref<string>) {
  /**
   * CEP sem máscara para consulta na API
   */
  const cleanCep = computed(() => unmaskCep(cep.value));

  return useQuery({
    queryKey: ['cep', cleanCep],
    queryFn: () => getAddressByCep(cleanCep.value),
    enabled: computed(() => cleanCep.value.length === CEP_LENGTH),
    staleTime: CEP_STALE_TIME,
    retry: CEP_RETRY_COUNT,
  });
}
