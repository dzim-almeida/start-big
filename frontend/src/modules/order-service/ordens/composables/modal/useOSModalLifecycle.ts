import { watch, type ComputedRef, type Ref } from 'vue';

import type { OSFormContext } from '../../types/context.type';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../../schemas/relationship/customer/customer.schema';
import type { OSReopenMode } from './useOSStatusLocks';

interface UseOSModalLifecycleParams {
  isOpen: ComputedRef<boolean>;
  ordemServico: ComputedRef<OrderServiceReadDataType | null | undefined>;
  selectedCliente: ComputedRef<CustomerUnionReadSchemaDataType | null | undefined>;
  currentOSData: ComputedRef<OrderServiceReadDataType | null>;
  localOSData: Ref<OrderServiceReadDataType | null>;
  isCreateMode: ComputedRef<boolean>;
  reopenMode: Ref<OSReopenMode>;
  form: OSFormContext;
  resetReopenState: () => void;
  onOpen: () => void;
}

export function useOSModalLifecycle({
  isOpen,
  ordemServico,
  selectedCliente,
  currentOSData,
  localOSData,
  isCreateMode,
  reopenMode,
  form,
  resetReopenState,
  onOpen,
}: UseOSModalLifecycleParams) {
  function populateEditForm(os: OrderServiceReadDataType) {
    form.atualizarGeral.populateForm(os);

    if (os.data_previsao) {
      form.atualizarGeral.data_previsao.value = os.data_previsao.split('T')[0];
    }

    form.atualizarEquipamento.populateForm({
      tipo_equipamento: os.equipamento.tipo_equipamento,
      marca: os.equipamento.marca,
      modelo: os.equipamento.modelo,
      numero_serie: os.equipamento.numero_serie,
      imei: os.equipamento.imei,
      cor: os.equipamento.cor,
      cliente_id: os.equipamento.cliente_id,
    });
  }

  watch(isOpen, (open) => {
    if (open) {
      onOpen();

      if (currentOSData.value) {
        populateEditForm(currentOSData.value);
      } else {
        form.criar.resetForm();
      }
      return;
    }

    resetReopenState();
    localOSData.value = null;
  }, { immediate: true });

  watch(() => currentOSData.value?.status, (newStatus, oldStatus) => {
    if (
      (oldStatus === 'FINALIZADA' || oldStatus === 'CANCELADA') &&
      newStatus === 'EM_ANDAMENTO' &&
      reopenMode.value === 'FULL'
    ) {
      form.atualizarGeral.status.value = 'EM_ANDAMENTO';
    }
  });

  watch(ordemServico, (os) => {
    localOSData.value = os ?? null;
  }, { immediate: true });

  watch(selectedCliente, (cliente) => {
    if (cliente && isCreateMode.value) {
      form.criar.cliente_id.value = (cliente as { id?: number }).id;
    }
  }, { immediate: true });
}
