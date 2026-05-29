import { inject, provide } from 'vue';
import type { ComputedRef, InjectionKey, Ref } from 'vue';

import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';
import type { CustomerUnionReadSchemaDataType } from '../schemas/relationship/customer/customer.schema';
import type {
  OsItemCreateSchemaDataType,
  OsItemReadSchemaDataType,
} from '../schemas/relationship/osItem.schema';
import type {
  OsPriorityEnumDataType,
  OsStatusEnumDataType,
} from '../schemas/enums/osEnums.schema';
import type { PendingPhoto } from '../components/form/OSFotoGallery.vue';
import type { EquipamentoFormData } from '../composables/modal/useOSFormAdapter';
import type { OSReopenMode } from '../composables/modal/useOSStatusLocks';
import type { PrintFormat } from '../composables/modal/useOSPrintFlow';

type OsItem = OsItemCreateSchemaDataType | OsItemReadSchemaDataType;

export interface OSFormViewContext {
  isOpen: ComputedRef<boolean>;
  currentOSData: ComputedRef<OrderServiceReadDataType | null>;
  currentCliente: ComputedRef<CustomerUnionReadSchemaDataType | null>;
  osNumber: ComputedRef<string | null>;
  isCreateMode: ComputedRef<boolean>;
  isEditMode: ComputedRef<boolean>;
  isPending: ComputedRef<boolean>;
  isFinalizada: ComputedRef<boolean>;
  isCancelada: ComputedRef<boolean>;
  reopenMode: Ref<OSReopenMode>;
  isStructureLocked: ComputedRef<boolean>;
  isItemsLocked: ComputedRef<boolean>;
  controlsStatus: ComputedRef<OsStatusEnumDataType>;
  controlsFuncionarioId: ComputedRef<string>;
  controlsPrioridade: ComputedRef<OsPriorityEnumDataType>;
  controlsDataPrevisao: ComputedRef<string>;
  statusOptions: ComputedRef<SelectOption[]>;
  prioridadeOptions: ComputedRef<SelectOption[]>;
  funcionariosOptions: ComputedRef<SelectOption[]>;
  displayItems: ComputedRef<OsItem[]>;
  displaySubtotal: ComputedRef<number>;
  displayValorEntrega: ComputedRef<number>;
  displayValorDesconto: ComputedRef<number>;
  displayValorTotal: ComputedRef<number>;
  displayValorEntrada: ComputedRef<number>;
  equipamentoFormData: ComputedRef<EquipamentoFormData>;
  equipamentosHistorico: Ref<EquipamentoHistorico[]>;
  selectedHistorico: Ref<string>;
  currentDiagnostico: ComputedRef<string>;
  pendingPhotos: Ref<PendingPhoto[]>;
  isReopenOptionsOpen: Ref<boolean>;
  printType: Ref<'ENTRADA' | 'SAIDA'>;
  printFormat: Ref<PrintFormat>;
  isPrintSelectModalOpen: Ref<boolean>;
  isFinalizarModalOpen: Ref<boolean>;
  isItemModalOpen: Ref<boolean>;
  editingItem: Ref<OsItemCreateSchemaDataType | null>;
  isEquipSelectModalOpen: Ref<boolean>;
  handleClose: () => void;
  handleLocalSubmit: () => void;
  handleFinalizarOS: () => void;
  printEntrada: () => void;
  printSaida: () => void;
  handleReopenClick: () => void;
  handleChangeCliente: () => void;
  handleUpdateCliente: (cliente: CustomerUnionReadSchemaDataType) => void;
  handleStatusUpdate: (value: OsStatusEnumDataType) => void;
  handleFuncionarioIdUpdate: (value: string) => void;
  handlePrioridadeUpdate: (value: OsPriorityEnumDataType) => void;
  handleDataPrevisaoUpdate: (value: string) => void;
  handleValorEntradaUpdate: (value: number) => void;
  setEquipamentoFormData: (value: EquipamentoFormData) => void;
  setSelectedHistorico: (value: string) => void;
  applyEquipamentoHistorico: () => void;
  handleDiagnosticoUpdate: (value: string) => void;
  handleAddPhoto: (file: File) => void;
  handleRemovePending: (index: number) => void;
  handlePhotoChange: () => void;
  openAddItemModal: () => void;
  openEditItemModal: (index: number) => void;
  handleRemoveItem: (index: number) => void;
  handleReopenCancel: () => void;
  handleReopenTextOnly: () => void;
  handleReopenFull: () => void;
  closeFinalizarModal: () => void;
  onFinalized: (payload: { shouldPrint: boolean }) => void;
  handlePrintFormatSelected: (format: PrintFormat) => void;
  closePrintSelectModal: () => void;
  closeItemModal: () => void;
  handleSaveItem: (item: OsItemCreateSchemaDataType) => void;
  closeEquipamentoModal: () => void;
  handleEquipamentoSelected: (equipamento: EquipamentoHistorico) => void;
  isHistoricoModalOpen: Ref<boolean>;
  openHistoricoModal: () => void;
  closeHistoricoModal: () => void;
  reutilizarEquipamento: (os: OrderServiceReadDataType) => void;
}

export const OS_FORM_VIEW_CONTEXT_KEY: InjectionKey<OSFormViewContext> = Symbol('os-form-view-context');

export function useOSFormViewProvider(context: OSFormViewContext): OSFormViewContext {
  provide(OS_FORM_VIEW_CONTEXT_KEY, context);
  return context;
}

export function useOSFormView(): OSFormViewContext {
  const context = inject(OS_FORM_VIEW_CONTEXT_KEY);

  if (!context) {
    throw new Error(
      '[useOSFormView] Contexto não encontrado. ' +
        'Certifique-se de que useOSFormViewProvider foi chamado em um componente ancestral.',
    );
  }

  return context;
}