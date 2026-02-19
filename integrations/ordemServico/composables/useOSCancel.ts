/**
 * ===========================================================================
 * ARQUIVO: useOSCancel.ts
 * MODULO: Ordem de Servico
 * DESCRICAO: Composable para gerenciar o formulario de cancelamento de OS.
 *            Controla validacao do motivo e opcao de impressao.
 * ===========================================================================
 *
 * FUNCIONALIDADES:
 * - Estado do motivo de cancelamento
 * - Validacao com Zod (minimo 5 caracteres)
 * - Opcao de imprimir comprovante de cancelamento
 * - Reset do formulario
 *
 * RETORNO:
 * - motivo: Texto do motivo de cancelamento
 * - shouldPrint: Flag para imprimir comprovante
 * - error: Mensagem de erro de validacao
 * - validate: Funcao de validacao
 * - reset: Limpa o formulario
 * ===========================================================================
 */
import { ref } from 'vue';
import { z } from 'zod';

export function useOSCancel() {
  const motivo = ref('');
  const shouldPrint = ref(false);
  const error = ref('');

  // Schema de validação simples
  const schema = z.string().min(5, "O motivo deve ter pelo menos 5 caracteres.");

  function validate(): boolean {
    const result = schema.safeParse(motivo.value.trim());
    if (!result.success) {
      error.value = result.error.errors[0].message;
      return false;
    }
    error.value = '';
    return true;
  }

  function reset() {
    motivo.value = '';
    shouldPrint.value = false;
    error.value = '';
  }

  return {
    motivo,
    shouldPrint,
    error,
    validate,
    reset
  };
}
