import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import type { Gender } from '@/modules/customers/types/clientes.types';

// =============================================
// Endereço padrão
// =============================================

export const DEFAULT_ADDRESS: AddressFormData = {
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  estado: '',
};

// =============================================
// Valores iniciais dos formulários
// =============================================

export const DEFAULT_PF_VALUES = {
  nome: '',
  cpf: '',
  rg: '',
  genero: '' as Gender | '',
  data_nascimento: '',
  email: '',
  celular: '',
  telefone: '',
  observacoes: '',
  enderecos: [{ ...DEFAULT_ADDRESS }] as AddressFormData[],
};

export const DEFAULT_PJ_VALUES = {
  razao_social: '',
  nome_fantasia: '',
  cnpj: '',
  ie: '',
  im: '',
  regime_tributario: '',
  responsavel: '',
  email: '',
  celular: '',
  telefone: '',
  observacoes: '',
  enderecos: [{ ...DEFAULT_ADDRESS }] as AddressFormData[],
};

// =============================================
// Opções de UI
// =============================================

export const CUSTOMER_TYPE_TABS = [
  { id: 'PF', label: 'Pessoa Física' },
  { id: 'PJ', label: 'Pessoa Jurídica' },
];

export const GENDER_OPTIONS = [
  { value: 'MASCULINO', label: 'Masculino' },
  { value: 'FEMININO', label: 'Feminino' },
  { value: 'OUTRO', label: 'Outro' },
];
