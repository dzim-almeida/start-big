/**
 * @fileoverview Tipos TypeScript para o módulo axios
 * @description Define as interfaces e tipos utilizados nas operações de erros
 * do axios
 */

/**
 * Interface para erro da API
 */
export interface ApiError {
  detail?: string;
  message?: string;
}
