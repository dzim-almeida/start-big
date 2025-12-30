/**
 * @fileoverview Utilitários para tratamento de erros
 * @description Funções helper para extrair e formatar mensagens de erro da API
 */

import type { AxiosError } from 'axios';
import type { ApiError, ValidationError } from '@/shared/types/axios.types';
import { ERROR_MESSAGES, NETWORK_ERROR_MESSAGE } from '@/shared/types/axios.types';

/**
 * Extrai a mensagem de erro de um ValidationError[]
 * @param errors - Array de erros de validação
 * @returns Mensagem formatada
 */
function formatValidationErrors(errors: ValidationError[]): string {
  if (errors.length === 0) return '';

  // Pega o primeiro erro e formata
  const firstError = errors[0];
  const field = firstError.loc[firstError.loc.length - 1];

  // Mapeia campos para nomes amigáveis
  const fieldNames: Record<string, string> = {
    email: 'Email',
    senha: 'Senha',
    nome: 'Nome',
    confirmarSenha: 'Confirmação de senha',
  };

  const fieldName = fieldNames[field as string] || field;
  return `${fieldName}: ${firstError.msg}`;
}

/**
 * Extrai mensagem de erro amigável de um AxiosError
 * @param error - Erro do Axios
 * @param defaultMessage - Mensagem padrão caso não encontre
 * @returns Mensagem de erro formatada para o usuário
 */
export function getErrorMessage(
  error: AxiosError<ApiError>,
  defaultMessage = 'Ocorreu um erro inesperado. Tente novamente.'
): string {
  // Erro de rede (sem resposta do servidor)
  if (!error.response) {
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      return NETWORK_ERROR_MESSAGE;
    }
    if (error.code === 'ECONNABORTED') {
      return 'A requisição demorou muito. Tente novamente.';
    }
    return defaultMessage;
  }

  const { status, data } = error.response;

  // Verifica se há mensagem específica da API
  if (data?.detail) {
    // Se detail for um array de ValidationError
    if (Array.isArray(data.detail)) {
      return formatValidationErrors(data.detail);
    }
    // Se detail for uma string
    return data.detail;
  }

  // Verifica campo message
  if (data?.message) {
    return data.message;
  }

  // Retorna mensagem baseada no status HTTP
  if (status && ERROR_MESSAGES[status]) {
    return ERROR_MESSAGES[status];
  }

  return defaultMessage;
}

/**
 * Verifica se é um erro de rede
 * @param error - Erro do Axios
 * @returns true se for erro de rede
 */
export function isNetworkError(error: AxiosError): boolean {
  return !error.response && (error.code === 'ERR_NETWORK' || error.message === 'Network Error');
}

/**
 * Verifica se é um erro de autenticação
 * @param error - Erro do Axios
 * @returns true se for erro 401
 */
export function isAuthError(error: AxiosError): boolean {
  return error.response?.status === 401;
}

/**
 * Verifica se é um erro de conflito (registro duplicado)
 * @param error - Erro do Axios
 * @returns true se for erro 409
 */
export function isConflictError(error: AxiosError): boolean {
  return error.response?.status === 409;
}
