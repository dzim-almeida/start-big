import { ref, watch, type ComputedRef, type Ref } from 'vue';

import { getClientEquipments } from '@/modules/customers/services/customerGet.service';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';

interface UseOSEquipmentHistoryParams {
  selectedCliente: ComputedRef<{ id?: number } | null | undefined>;
  ordemServicoCliente: ComputedRef<{ id?: number } | null | undefined>;
  isCreateMode: ComputedRef<boolean>;
  createEquipamentoTipo: Ref<string | undefined>;
  createEquipamentoMarca: Ref<string | undefined>;
  createEquipamentoModelo: Ref<string | undefined>;
  createEquipamentoNumeroSerie: Ref<string | undefined>;
}

export function useOSEquipmentHistory({
  selectedCliente,
  ordemServicoCliente,
  isCreateMode,
  createEquipamentoTipo,
  createEquipamentoMarca,
  createEquipamentoModelo,
  createEquipamentoNumeroSerie,
}: UseOSEquipmentHistoryParams) {
  const equipamentosHistorico = ref<EquipamentoHistorico[]>([]);
  const selectedHistorico = ref<string>('');
  const isEquipSelectModalOpen = ref(false);

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
        !createEquipamentoTipo.value
      ) {
        isEquipSelectModalOpen.value = true;
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

  watch(
    () => [selectedCliente.value?.id, ordemServicoCliente.value?.id],
    fetchEquipamentosHistorico,
    { immediate: true },
  );

  return {
    equipamentosHistorico,
    selectedHistorico,
    isEquipSelectModalOpen,
    handleEquipamentoSelected,
    applyEquipamentoHistorico,
  };
}
