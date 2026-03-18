import type { ComputedRef, Ref } from 'vue';
import type { FieldEntry } from 'vee-validate';

import type { OsItemCreateSchemaDataType, OsItemUpdateSchemaDataType } from '../schemas/relationship/osItem.schema';
import type { OsEquipUpdateSchemaDataType } from '../schemas/relationship/osEquip.schema';
import type { OsPaymentCreateSchemaDataType } from '../schemas/relationship/osPayment.schema';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';


export interface OSCreateFormContext {
  // Campos gerais
  prioridade: Ref<string | undefined>;
  defeito_relatado: Ref<string | undefined>;
  diagnostico: Ref<string | undefined>;
  observacoes: Ref<string | undefined>;
  desconto: Ref<number | undefined>;
  garantia: Ref<string | undefined>;
  data_previsao: Ref<string | undefined>;
  senha_aparelho: Ref<string | undefined>;
  acessorios: Ref<string | undefined>;
  condicoes_aparelho: Ref<string | undefined>;

  // Vínculos
  cliente_id: Ref<number | undefined>;
  funcionario_id: Ref<number | undefined>;

  // Campos do equipamento (nested via dot-notation)
  equipamento_tipo_equipamento: Ref<string | undefined>;
  equipamento_marca: Ref<string | undefined>;
  equipamento_modelo: Ref<string | undefined>;
  equipamento_numero_serie: Ref<string | undefined>;
  equipamento_imei: Ref<string | undefined>;
  equipamento_cor: Ref<string | undefined>;

  // FieldArray de itens iniciais
  itens: Ref<FieldEntry<OsItemCreateSchemaDataType>[]>;
  handleAddItem: (item?: Partial<OsItemCreateSchemaDataType>) => void;
  handleRemoveItem: (index: number) => void;
  handleUpdateItem: (index: number, item: OsItemCreateSchemaDataType) => void;

  // Estado do formulário
  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  // Ações
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}


export interface OSUpdateGeralFormContext {
  status: Ref<string | undefined>;
  prioridade: Ref<string | undefined>;
  defeito_relatado: Ref<string | undefined>;
  diagnostico: Ref<string | undefined>;
  solucao: Ref<string | undefined>;
  observacoes: Ref<string | undefined>;
  desconto: Ref<number | undefined>;
  garantia: Ref<string | undefined>;
  data_previsao: Ref<string | undefined>;
  senha_aparelho: Ref<string | undefined>;
  acessorios: Ref<string | undefined>;
  condicoes_aparelho: Ref<string | undefined>;
  funcionario_id: Ref<number | undefined>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
  populateForm: (os: OrderServiceReadDataType) => void;
}


export interface OSUpdateEquipFormContext {
  tipo_equipamento: Ref<string | undefined>;
  marca: Ref<string | undefined>;
  modelo: Ref<string | undefined>;
  numero_serie: Ref<string | undefined>;
  imei: Ref<string | undefined>;
  cor: Ref<string | undefined>;
  cliente_id: Ref<number | undefined>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
  populateForm: (equip: OsEquipUpdateSchemaDataType) => void;
}


export interface OSItemFormContext {
  tipo: Ref<string | undefined>;
  nome: Ref<string | undefined>;
  unidade_medida: Ref<string | undefined>;
  quantidade: Ref<number | undefined>;
  valor_unitario: Ref<number | undefined>;

  
  editingItemId: Ref<number | null>;
  isEditMode: ComputedRef<boolean>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  
  setEditingItem: (itemId: number, itemData: OsItemUpdateSchemaDataType) => void;
  resetForm: () => void;
}


export interface OSFinalizarFormContext {
  solucao: Ref<string | undefined>;
  observacoes: Ref<string | undefined>;
  desconto: Ref<number | undefined>;

  pagamentos: Ref<FieldEntry<OsPaymentCreateSchemaDataType>[]>;
  handleAddPagamento: (pagamento?: Partial<OsPaymentCreateSchemaDataType>) => void;
  handleRemovePagamento: (index: number) => void;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}


export interface OSCancelarFormContext {
  motivo: Ref<string | undefined>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}

export interface OSFormContext {
  // Número da OS sendo editada (null em modo criação)
  currentOsNumber: Ref<string | null>;
  isCreateMode: ComputedRef<boolean>;

  criar: OSCreateFormContext;
  atualizarGeral: OSUpdateGeralFormContext;
  atualizarEquipamento: OSUpdateEquipFormContext;
  item: OSItemFormContext;
  finalizar: OSFinalizarFormContext;
  cancelar: OSCancelarFormContext;
}
