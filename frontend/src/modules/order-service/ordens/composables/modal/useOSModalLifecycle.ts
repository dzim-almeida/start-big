import { watch, type ComputedRef, type Ref } from 'vue';

import type { OSFormContext } from '../../types/context.type';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../../schemas/relationship/customer/customer.schema';
import type { OsEquipTypeEnumDataType } from '../../schemas/enums/osEnums.schema';
import type { OSReopenMode } from './useOSStatusLocks';
import { useAuthStore } from '@/shared/stores/auth.store';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';

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
  form,
  resetReopenState,
  onOpen,
}: UseOSModalLifecycleParams) {
  const authStore = useAuthStore();
  const configStore = useConfiguracoesStore();

  function populateEditForm(os: OrderServiceReadDataType) {
    form.atualizarGeral.populateForm(os);

    if (os.data_previsao) {
      form.atualizarGeral.data_previsao.value = os.data_previsao.split('T')[0];
    }

    form.atualizarObjeto.populateForm({
      // Read é string livre por segmento; para informática é sempre um valor do enum.
      tipo_equipamento: (os.objeto.tipo_equipamento ?? undefined) as OsEquipTypeEnumDataType | undefined,
      marca: os.objeto.marca,
      modelo: os.objeto.modelo,
      numero_serie: os.objeto.numero_serie,
      imei: os.objeto.imei,
      cor: os.objeto.cor,
      cliente_id: os.objeto.cliente_id,
    });
  }

  watch(isOpen, (open) => {
    if (open) {
      onOpen();

      if (currentOSData.value) {
        populateEditForm(currentOSData.value);
      } else {
        form.criar.resetForm();
        if (authStore.userData?.funcionario_id) {
          form.criar.funcionario_id.value = authStore.userData.funcionario_id;
        }
        const prazo = configStore.prazoEntregaPadrao;
        if (prazo > 0) {
          const previsao = new Date();
          previsao.setDate(previsao.getDate() + prazo);
          form.criar.data_previsao.value = previsao.toISOString().split('T')[0];
        }

        const taxa = configStore.taxaDiagnosticoPadrao;
        if (taxa > 0) {
          form.criar.handleAddItem({
            tipo: 'SERVICO',
            nome: 'Diagnóstico',
            unidade_medida: 'UN',
            quantidade: 1,
            valor_unitario: taxa,
          });
        }
      }
      return;
    }

    resetReopenState();
    localOSData.value = null;
  }, { immediate: true });

  watch(() => currentOSData.value?.status, (newStatus, oldStatus) => {
    if (
      (oldStatus === 'FINALIZADA' || oldStatus === 'CANCELADA') &&
      newStatus === 'EM_ANDAMENTO'
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
