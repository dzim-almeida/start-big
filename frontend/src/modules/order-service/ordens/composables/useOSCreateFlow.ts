import { ref } from 'vue';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../schemas/relationship/customer/customer.schema';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';
import { getClientEquipments } from '@/modules/customers/services/customerGet.service';

// =============================================
// Shared State (singleton pattern)
// =============================================

const isClienteSearchOpen = ref(false);
const isFormModalOpen = ref(false);
const isEquipSelectOpen = ref(false);
const selectedCliente = ref<CustomerUnionReadSchemaDataType | null>(null);
const selectedOS = ref<OrderServiceReadDataType | null>(null);
const equipamentosHistoricoFlow = ref<EquipamentoHistorico[]>([]);
const selectedEquipamento = ref<EquipamentoHistorico | null>(null);

// =============================================
// Composable
// =============================================

export function useOSCreateFlow() {
  function openNovaOS() {
    selectedOS.value = null;
    selectedCliente.value = null;
    selectedEquipamento.value = null;
    isClienteSearchOpen.value = true;
  }

  function openExistingOS(os: OrderServiceReadDataType) {
    selectedOS.value = os;
    selectedCliente.value = null;
    selectedEquipamento.value = null;
    isFormModalOpen.value = true;
  }

  async function handleClienteSelected(cliente: CustomerUnionReadSchemaDataType) {
    selectedCliente.value = cliente;
    selectedEquipamento.value = null;
    isClienteSearchOpen.value = false;

    try {
      const history = await getClientEquipments(cliente.id);
      if (history.length > 0) {
        equipamentosHistoricoFlow.value = history;
        isEquipSelectOpen.value = true;
        return;
      }
    } catch {
      // histórico de equipamentos é opcional
    }

    isFormModalOpen.value = true;
  }

  function handleEquipamentoSelectedFlow(equip: EquipamentoHistorico) {
    selectedEquipamento.value = equip;
    isEquipSelectOpen.value = false;
    isFormModalOpen.value = true;
  }

  function skipEquipamentoSelectFlow() {
    selectedEquipamento.value = null;
    isEquipSelectOpen.value = false;
    isFormModalOpen.value = true;
  }

  function handleChangeCliente() {
    isFormModalOpen.value = false;
    isClienteSearchOpen.value = true;
  }

  function closeClienteSearch() {
    isClienteSearchOpen.value = false;
  }

  function closeFormModal() {
    isFormModalOpen.value = false;
    selectedOS.value = null;
    selectedCliente.value = null;
    selectedEquipamento.value = null;
    equipamentosHistoricoFlow.value = [];
  }

  return {
    isClienteSearchOpen,
    isFormModalOpen,
    isEquipSelectOpen,
    selectedCliente,
    selectedOS,
    equipamentosHistoricoFlow,
    selectedEquipamento,
    openNovaOS,
    openExistingOS,
    handleClienteSelected,
    handleEquipamentoSelectedFlow,
    skipEquipamentoSelectFlow,
    handleChangeCliente,
    closeClienteSearch,
    closeFormModal,
  };
}
