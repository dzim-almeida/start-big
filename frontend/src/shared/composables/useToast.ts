/**
 * @fileoverview Composable para exibição de toasts
 * @description Wrapper do vue-sonner com métodos tipados e configurações padrão
 */

import { toast } from 'vue-sonner';

/**
 * Composable para gerenciar notificações toast
 * @returns Métodos para exibir diferentes tipos de toast
 */
export function useToast() {
  /**
   * Exibe toast de sucesso
   * @param message - Mensagem a ser exibida
   * @param description - Descrição opcional
   */
  const success = (message: string, description?: string) => {
    toast.success(message, { description });
  };

  /**
   * Exibe toast de erro
   * @param message - Mensagem a ser exibida
   * @param description - Descrição opcional
   */
  const error = (message: string, description?: string) => {
    toast.error(message, { description });
  };

  /**
   * Exibe toast de aviso
   * @param message - Mensagem a ser exibida
   * @param description - Descrição opcional
   */
  const warning = (message: string, description?: string) => {
    toast.warning(message, { description });
  };

  /**
   * Exibe toast informativo
   * @param message - Mensagem a ser exibida
   * @param description - Descrição opcional
   */
  const info = (message: string, description?: string) => {
    toast.info(message, { description });
  };

  /**
   * Exibe toast com promise (loading -> success/error)
   * @param promise - Promise a ser aguardada
   * @param messages - Mensagens para cada estado
   */
  const promise = <T>(
    promiseFn: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    return toast.promise(promiseFn, messages);
  };

  return {
    success,
    error,
    warning,
    info,
    promise,
  };
}
