import { ref } from 'vue';

import type { EquipamentoFormData } from './useOSFormAdapter';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';

interface UseOSClientHistoryParams {
  setEquipamentoFormData: (value: EquipamentoFormData) => void;
}

export function useOSClientHistory({ setEquipamentoFormData }: UseOSClientHistoryParams) {
  const isHistoricoModalOpen = ref(false);

  function openHistoricoModal() {
    isHistoricoModalOpen.value = true;
  }

  function closeHistoricoModal() {
    isHistoricoModalOpen.value = false;
  }

  function reutilizarEquipamento(os: OrderServiceReadDataType) {
    const equip = os.equipamento;
    setEquipamentoFormData({
      equipamento: equip.tipo_equipamento,
      marca: equip.marca ?? '',
      modelo: equip.modelo ?? '',
      numero_serie: equip.numero_serie ?? '',
      imei: equip.imei ?? '',
      cor: equip.cor ?? '',
      senha_aparelho: '',
      acessorios: '',
      defeito_relatado: '',
      condicoes_aparelho: '',
    });
    closeHistoricoModal();
  }

  return {
    isHistoricoModalOpen,
    openHistoricoModal,
    closeHistoricoModal,
    reutilizarEquipamento,
  };
}
