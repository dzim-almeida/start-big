/**
 * @fileoverview Composable para busca de CEP
 * @description Encapsula a lógica de consulta de CEP usando a API ViaCEP
 * com debounce e tratamento de erros.
 */

import { ref } from 'vue';
import { fetchAddressByCep } from '../services/onboarding.service';
import type { ViaCepResponse } from '../types/onboarding.types';

/**
 * Composable para busca automática de endereço por CEP
 * @returns Objeto com estados e métodos para consulta de CEP
 */
export function useCepLookup() {
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const addressData = ref<ViaCepResponse | null>(null);

  /**
   * Busca endereço pelo CEP
   * @param cep - CEP a ser consultado
   * @returns Promise com os dados do endereço ou null
   */
  async function lookupCep(cep: string): Promise<ViaCepResponse | null> {
    const cleanCep = cep.replace(/\D/g, '');

    if (cleanCep.length !== 8) {
      error.value = null;
      addressData.value = null;
      return null;
    }

    isLoading.value = true;
    error.value = null;

    try {
      const data = await fetchAddressByCep(cleanCep);
      addressData.value = data;
      return data;
    } catch (err) {
      error.value = 'CEP não encontrado';
      addressData.value = null;
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Limpa os dados da consulta
   */
  function clearLookup(): void {
    error.value = null;
    addressData.value = null;
  }

  return {
    isLoading,
    error,
    addressData,
    lookupCep,
    clearLookup,
  };
}
