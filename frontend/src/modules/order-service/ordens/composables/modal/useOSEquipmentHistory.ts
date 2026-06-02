import { ref, watch, type ComputedRef, type Ref } from 'vue';

import { getClientEquipments } from '@/modules/customers/services/customerGet.service';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';

interface UseOSEquipmentHistoryParams {
  selectedCliente: ComputedRef<{ id?: number } | null | undefined>;
  ordemServicoCliente: ComputedRef<{ id?: number } | null | undefined>;
  isCreateMode: ComputedRef<boolean>;
  isFormOpen: ComputedRef<boolean>;
  createEquipamentoTipo: Ref<string | null | undefined>;
  createEquipamentoMarca: Ref<string | null | undefined>;
  createEquipamentoModelo: Ref<string | null | undefined>;
  createEquipamentoNumeroSerie: Ref<string | null | undefined>;
}

export function useOSEquipmentHistory({
  selectedCliente,
  ordemServicoCliente,
  isCreateMode,
  isFormOpen,
  createEquipamentoTipo,
  createEquipamentoMarca,
  createEquipamentoModelo,
  createEquipamentoNumeroSerie,
}: UseOSEquipmentHistoryParams) {
  const equipamentosHistorico = ref<EquipamentoHistorico[]>([]);
  const selectedHistorico = ref<string>('');
  const isEquipSelectModalOpen = ref(false);
  const wasEquipSelectShown = ref(false);
  const lastShownClientId = ref<number | null>(null);

  async function fetchEquipamentosHistorico() {
    const clienteId = selectedCliente.value?.id ?? ordemServicoCliente.value?.id;
    if (!clienteId) {
      equipamentosHistorico.value = [];
      return;
    }

    try {
      const history = await getClientEquipments(clienteId);
      equipamentosHistorico.value = history;

      if (
        history.length > 0 &&
        isCreateMode.value &&
        isFormOpen.value &&
        !createEquipamentoTipo.value &&
        !wasEquipSelectShown.value
      ) {
        isEquipSelectModalOpen.value = true;
        wasEquipSelectShown.value = true;
        lastShownClientId.value = clienteId ?? null;
      }
    } catch {
      // histórico de equipamentos é opcional
    }
  }

  function handleEquipamentoSelected(equipamento: EquipamentoHistorico) {
    if (isCreateMode.value) {
      createEquipamentoTipo.value = equipamento.equipamento;
      createEquipamentoMarca.value = equipamento.marca || '';
      createEquipamentoModelo.value = equipamento.modelo || '';
      createEquipamentoNumeroSerie.value = equipamento.numero_serie || '';
    }

    const selectedIndex = equipamentosHistorico.value.findIndex(
      (item) =>
        item.numero_serie === equipamento.numero_serie &&
        item.equipamento === equipamento.equipamento,
    );

    if (selectedIndex !== -1) {
      selectedHistorico.value = String(selectedIndex);
    }

    isEquipSelectModalOpen.value = false;
  }

  function applyEquipamentoHistorico() {
    if (!selectedHistorico.value) return;

    const equipamento = equipamentosHistorico.value[parseInt(selectedHistorico.value, 10)];
    if (equipamento) {
      handleEquipamentoSelected(equipamento);
    }
  }

  function resetEquipSelectState() {
    wasEquipSelectShown.value = false;
    isEquipSelectModalOpen.value = false;
  }

  watch(
    () => [selectedCliente.value?.id, ordemServicoCliente.value?.id],
    ([newClientId]) => {
      const clientId = newClientId as number | undefined;
      if (clientId && clientId !== lastShownClientId.value) {
        wasEquipSelectShown.value = false;
      }
      fetchEquipamentosHistorico();
    },
    { immediate: true },
  );

  return {
    equipamentosHistorico,
    selectedHistorico,
    isEquipSelectModalOpen,
    handleEquipamentoSelected,
    applyEquipamentoHistorico,
    resetEquipSelectState,
  };
}
