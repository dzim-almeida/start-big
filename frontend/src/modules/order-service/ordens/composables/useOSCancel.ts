import { ref } from 'vue';
import { z } from 'zod';

export function useOSCancel() {
  const motivo = ref('');
  const shouldPrint = ref(false);
  const error = ref('');

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
    reset,
  };
}
