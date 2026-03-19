import { computed } from 'vue';
import { useCancelOrderServiceMutation } from './request/useOrderServiceUpdate.mutate';

export function useOSActions() {
  const cancelMutation = useCancelOrderServiceMutation();

  // Adapter: o tab passa { id: numero_os, motivo } mas a mutation espera { osNumber, cancelOs }
  const cancelarMutation = {
    mutate: (
      payload: { id: string; motivo: string },
      options?: Parameters<typeof cancelMutation.mutate>[1],
    ) => {
      cancelMutation.mutate(
        { osNumber: payload.id, cancelOs: { motivo: payload.motivo } },
        options,
      );
    },
    isPending: cancelMutation.isPending,
  };

  const isPending = computed(() => cancelMutation.isPending.value);

  return {
    cancelarMutation,
    isPending,
  };
}
