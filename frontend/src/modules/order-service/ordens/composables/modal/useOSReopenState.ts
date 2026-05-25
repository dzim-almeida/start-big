import { ref, type ComputedRef } from 'vue';

import type { OSReopenMode } from './useOSStatusLocks';

interface UseOSReopenStateParams {
  osNumber: ComputedRef<string | null>;
  onReopenRequest: (osNumber: string) => void;
  onFullReopen: () => void;
}

export function useOSReopenState({
  osNumber,
  onReopenRequest,
  onFullReopen,
}: UseOSReopenStateParams) {
  const isReopenOptionsOpen = ref(false);
  const reopenMode = ref<OSReopenMode>('NONE');

  function handleReopenClick() {
    isReopenOptionsOpen.value = true;
  }

  function handleReopenCancel() {
    isReopenOptionsOpen.value = false;
    reopenMode.value = 'NONE';
  }

  function handleReopenTextOnly() {
    const currentOsNumber = osNumber.value;
    if (!currentOsNumber) return;

    reopenMode.value = 'TEXT_ONLY';
    isReopenOptionsOpen.value = false;
    onReopenRequest(currentOsNumber);
  }

  function handleReopenFull() {
    const currentOsNumber = osNumber.value;
    if (!currentOsNumber) return;

    reopenMode.value = 'FULL';
    isReopenOptionsOpen.value = false;
    onReopenRequest(currentOsNumber);
    onFullReopen();
  }

  function resetReopenState() {
    reopenMode.value = 'NONE';
    isReopenOptionsOpen.value = false;
  }

  return {
    isReopenOptionsOpen,
    reopenMode,
    handleReopenClick,
    handleReopenCancel,
    handleReopenTextOnly,
    handleReopenFull,
    resetReopenState,
  };
}
