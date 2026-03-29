import type { ComputedRef, Ref } from 'vue';
import type { FieldEntry } from 'vee-validate';
import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import type { TipoCliente } from '@/modules/customers/types/clientes.types';

/**
 * Contexto agregado do formulário de cliente.
 * Provido via provide/inject pelo CustomerFormModal.
 * Consumido pelos child components (PersonalDataSection, CompanyDataSection, etc.)
 */
export interface CustomerFormContext {
  // Tipo de cliente (PF/PJ)
  customerType: Ref<TipoCliente>;
  setCustomerType: (type: TipoCliente) => void;

  // Campos PF
  nome: Ref<string | undefined>;
  cpf: Ref<string | undefined>;
  rg: Ref<string | undefined>;
  genero: Ref<string | undefined>;
  data_nascimento: Ref<string | undefined>;

  // Campos PJ
  razao_social: Ref<string | undefined>;
  nome_fantasia: Ref<string | undefined>;
  cnpj: Ref<string | undefined>;
  ie: Ref<string | undefined>;
  im: Ref<string | undefined>;
  regime_tributario: Ref<string | undefined>;
  responsavel: Ref<string | undefined>;

  // Campos comuns (computed — alternam por customerType)
  email: Ref<string | undefined>;
  celular: Ref<string | undefined>;
  telefone: Ref<string | undefined>;
  observacoes: Ref<string | undefined>;

  // Endereços (alternam por customerType)
  enderecos: Ref<FieldEntry<AddressFormData>[]>;
  handleAddAddress: () => void;
  handleRemoveAddress: (index: number) => void;

  // Estado do formulário
  errors: Ref<Record<string, string | undefined>>;
  submitCount: Ref<number>;
  apiError: Ref<string | null>;
  isPending: ComputedRef<boolean>;

  // Ações
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}
