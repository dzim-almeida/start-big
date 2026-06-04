import type { ComputedRef, Ref } from 'vue';
import type { FieldEntry } from 'vee-validate';

import type { OsItemCreateSchemaDataType, OsItemUpdateSchemaDataType } from '../schemas/relationship/osItem.schema';
import type { OsEquipUpdateSchemaDataType } from '../schemas/relationship/osEquip.schema';
import type { OsPaymentCreateSchemaDataType } from '../schemas/relationship/osPayment.schema';
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema';


export interface OSCreateFormContext {
  // Campos gerais
  prioridade: Ref<string | null | undefined>;
  defeito_relatado: Ref<string | null | undefined>;
  diagnostico: Ref<string | null | undefined>;
  observacoes: Ref<string | null | undefined>;
  desconto: Ref<number | null | undefined>;
  valor_entrada: Ref<number | null | undefined>;
  garantia: Ref<string | null | undefined>;
  data_previsao: Ref<string | null | undefined>;
  senha_aparelho: Ref<string | null | undefined>;
  acessorios: Ref<string | null | undefined>;
  condicoes_aparelho: Ref<string | null | undefined>;

  // Vínculos
  cliente_id: Ref<number | null | undefined>;
  funcionario_id: Ref<number | null | undefined>;

  // Campos do equipamento (nested via dot-notation)
  equipamento_tipo_equipamento: Ref<string | null | undefined>;
  equipamento_marca: Ref<string | null | undefined>;
  equipamento_modelo: Ref<string | null | undefined>;
  equipamento_numero_serie: Ref<string | null | undefined>;
  equipamento_imei: Ref<string | null | undefined>;
  equipamento_cor: Ref<string | null | undefined>;

  // FieldArray de itens iniciais
  itens: Ref<FieldEntry<OsItemCreateSchemaDataType>[]>;
  handleAddItem: (item?: Partial<OsItemCreateSchemaDataType>) => void;
  handleRemoveItem: (index: number) => void;
  handleUpdateItem: (index: number, item: OsItemCreateSchemaDataType) => void;

  // Crédito
  usar_credito_cliente: Ref<boolean>;

  // Estado do formulário
  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  // Ações
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}


export interface OSUpdateGeralFormContext {
  status: Ref<string | null | undefined>;
  prioridade: Ref<string | null | undefined>;
  defeito_relatado: Ref<string | null | undefined>;
  diagnostico: Ref<string | null | undefined>;
  solucao: Ref<string | null | undefined>;
  observacoes: Ref<string | null | undefined>;
  desconto: Ref<number | null | undefined>;
  valor_entrada: Ref<number | null | undefined>;
  taxa_entrega: Ref<number | null | undefined>;
  garantia: Ref<string | null | undefined>;
  data_previsao: Ref<string | null | undefined>;
  senha_aparelho: Ref<string | null | undefined>;
  acessorios: Ref<string | null | undefined>;
  condicoes_aparelho: Ref<string | null | undefined>;
  funcionario_id: Ref<number | null | undefined>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  onSubmitTextOnly: () => void;
  resetForm: () => void;
  populateForm: (os: OrderServiceReadDataType) => void;
}


export interface OSUpdateEquipFormContext {
  tipo_equipamento: Ref<string | null | undefined>;
  marca: Ref<string | null | undefined>;
  modelo: Ref<string | null | undefined>;
  numero_serie: Ref<string | null | undefined>;
  imei: Ref<string | null | undefined>;
  cor: Ref<string | null | undefined>;
  cliente_id: Ref<number | null | undefined>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
  populateForm: (equip: OsEquipUpdateSchemaDataType) => void;
}


export interface OSItemFormContext {
  tipo: Ref<string | null | undefined>;
  nome: Ref<string | null | undefined>;
  unidade_medida: Ref<string | null | undefined>;
  quantidade: Ref<number | null | undefined>;
  valor_unitario: Ref<number | null | undefined>;

  editingItemId: Ref<number | null>;
  isEditMode: ComputedRef<boolean>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;

  setEditingItem: (itemId: number, itemData: OsItemUpdateSchemaDataType) => void;
  resetForm: () => void;
}


export interface OSFinalizarFormContext {
  situacao_equipamento: Ref<string | null | undefined>;
  solucao: Ref<string | null | undefined>;
  observacoes: Ref<string | null | undefined>;
  desconto: Ref<number | null | undefined>;
  taxa_entrega: Ref<number | null | undefined>;
  acrescimo: Ref<number | null | undefined>;
  valor_entrada: Ref<number | null | undefined>;

  pagamentos: Ref<FieldEntry<OsPaymentCreateSchemaDataType>[]>;
  handleAddPagamento: (pagamento?: Partial<OsPaymentCreateSchemaDataType>) => void;
  handleRemovePagamento: (index: number) => void;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}


export interface OSCancelarFormContext {
  motivo: Ref<string | null | undefined>;

  errors: Ref<Record<string, string | undefined>>;
  isPending: ComputedRef<boolean>;

  onSubmit: (e?: Event) => void;
  submitDireto: (zerar: boolean) => void;
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
