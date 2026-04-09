import { computed, type ComputedRef, type Ref } from 'vue';

export type OSReopenMode = 'NONE' | 'TEXT_ONLY' | 'FULL';

interface UseOSStatusLocksParams {
  isFinalizada: ComputedRef<boolean>;
  isCancelada: ComputedRef<boolean>;
  reopenMode: Ref<OSReopenMode>;
}

export function useOSStatusLocks({
  isFinalizada,
  isCancelada,
  reopenMode,
}: UseOSStatusLocksParams) {
  const isLocked = computed(() => isFinalizada.value || isCancelada.value);
  const isStructureLocked = computed(() => isLocked.value && reopenMode.value === 'NONE');
  const isItemsLocked = computed(() => isLocked.value || reopenMode.value === 'TEXT_ONLY');

  return {
    isLocked,
    isStructureLocked,
    isItemsLocked,
  };
}
