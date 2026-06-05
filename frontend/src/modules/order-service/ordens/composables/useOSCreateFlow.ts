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
const isCreditAlertOpen = ref(false);
const selectedCliente = ref<CustomerUnionReadSchemaDataType | null>(null);
const selectedOS = ref<OrderServiceReadDataType | null>(null);
const equipamentosHistoricoFlow = ref<EquipamentoHistorico[]>([]);
const selectedEquipamento = ref<EquipamentoHistorico | null>(null);
const autoUsarCredito = ref(false);

// =============================================
// Helper privado — continua o fluxo após a decisão de crédito
// =============================================

async function _continuarFluxoCliente() {
  const cliente = selectedCliente.value;
  if (!cliente) return;

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

// =============================================
// Composable
// =============================================

export function useOSCreateFlow() {
  function openNovaOS() {
    selectedOS.value = null;
    selectedCliente.value = null;
    selectedEquipamento.value = null;
    autoUsarCredito.value = false;
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

    const saldo = (cliente as { saldo_credito?: number }).saldo_credito ?? 0;
    if (saldo > 0) {
      isCreditAlertOpen.value = true;
      return;
    }

    await _continuarFluxoCliente();
  }

  async function handleCreditoUsado() {
    autoUsarCredito.value = true;
    isCreditAlertOpen.value = false;
    await _continuarFluxoCliente();
  }

  async function handleCreditoIgnorado() {
    autoUsarCredito.value = false;
    isCreditAlertOpen.value = false;
    await _continuarFluxoCliente();
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
    autoUsarCredito.value = false;
  }

  return {
    isClienteSearchOpen,
    isFormModalOpen,
    isEquipSelectOpen,
    isCreditAlertOpen,
    selectedCliente,
    selectedOS,
    equipamentosHistoricoFlow,
    selectedEquipamento,
    autoUsarCredito,
    openNovaOS,
    openExistingOS,
    handleClienteSelected,
    handleCreditoUsado,
    handleCreditoIgnorado,
    handleEquipamentoSelectedFlow,
    skipEquipamentoSelectFlow,
    handleChangeCliente,
    closeClienteSearch,
    closeFormModal,
  };
}
