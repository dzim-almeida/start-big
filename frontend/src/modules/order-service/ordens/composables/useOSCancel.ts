import { ref } from 'vue';

export function useOSCancel() {
  const motivo = ref('');
  const shouldPrint = ref(false);
  const error = ref<string | null>(null);

  function validate(): boolean {
    if (!motivo.value.trim()) {
      error.value = 'O motivo do cancelamento é obrigatório.';
      return false;
    }
    error.value = null;
    return true;
  }

  function reset() {
    motivo.value = '';
    shouldPrint.value = false;
    error.value = null;
  }

  return {
    motivo,
    shouldPrint,
    error,
    validate,
    reset,
  };
}
