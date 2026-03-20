import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import type {
  CustomerPFCreateDataType,
  CustomerPJCreateDataType,
  CustomerPFUpdateDataType,
  CustomerPJUpdateDataType,
} from '@/modules/customers/schemas/customerMutate.schema';
import { GenderTypeEnum } from '@/shared/schemas/customer/enums/genderEnum.schema';
import { unmaskDocument, unmaskPhone } from '@/shared/utils/unmask.utils';
import { prepareAddresses } from './address.helpers';

// =============================================
// Tipos dos values de cada formulário
// =============================================

export interface PFFormValues {
  nome?: string;
  cpf?: string;
  rg?: string;
  genero?: string;
  data_nascimento?: string;
  email?: string;
  celular?: string;
  telefone?: string;
  observacoes?: string;
  enderecos?: Partial<AddressFormData>[];
}

export interface PJFormValues {
  razao_social?: string;
  nome_fantasia?: string;
  cnpj?: string;
  ie?: string;
  im?: string;
  regime_tributario?: string;
  responsavel?: string;
  email?: string;
  celular?: string;
  telefone?: string;
  observacoes?: string;
  enderecos?: Partial<AddressFormData>[];
}

// =============================================
// Helpers
// =============================================

function parseGender(value: string | undefined) {
  const result = GenderTypeEnum.safeParse(value);
  return result.success ? result.data : undefined;
}

// =============================================
// Transformers PF
// =============================================

export function transformPFToCreateRequest(formData: PFFormValues): CustomerPFCreateDataType {
  return {
    nome: formData.nome!,
    cpf: unmaskDocument(formData.cpf || '') || undefined,
    rg: unmaskDocument(formData.rg || '') || undefined,
    genero: parseGender(formData.genero),
    data_nascimento: formData.data_nascimento || undefined,
    email: formData.email || undefined,
    celular: unmaskPhone(formData.celular || '') || undefined,
    telefone: unmaskPhone(formData.telefone || '') || undefined,
    observacoes: formData.observacoes || undefined,
    endereco: prepareAddresses(formData.enderecos || [], false),
  };
}

export function transformPFToUpdateRequest(formData: PFFormValues): CustomerPFUpdateDataType {
  return {
    tipo: 'PF',
    nome: formData.nome || undefined,
    cpf: unmaskDocument(formData.cpf || '') || undefined,
    rg: unmaskDocument(formData.rg || '') || undefined,
    genero: parseGender(formData.genero),
    data_nascimento: formData.data_nascimento || undefined,
    email: formData.email || undefined,
    celular: unmaskPhone(formData.celular || '') || undefined,
    telefone: unmaskPhone(formData.telefone || '') || undefined,
    observacoes: formData.observacoes || undefined,
    endereco: prepareAddresses(formData.enderecos || [], true),
  };
}

// =============================================
// Transformers PJ
// =============================================

export function transformPJToCreateRequest(formData: PJFormValues): CustomerPJCreateDataType {
  return {
    razao_social: formData.razao_social!,
    nome_fantasia: formData.nome_fantasia || undefined,
    cnpj: unmaskDocument(formData.cnpj || '') || undefined,
    ie: formData.ie || undefined,
    im: formData.im || undefined,
    regime_tributario: formData.regime_tributario || undefined,
    responsavel: formData.responsavel || undefined,
    email: formData.email || undefined,
    celular: unmaskPhone(formData.celular || '') || undefined,
    telefone: unmaskPhone(formData.telefone || '') || undefined,
    observacoes: formData.observacoes || undefined,
    endereco: prepareAddresses(formData.enderecos || [], false),
  };
}

export function transformPJToUpdateRequest(formData: PJFormValues): CustomerPJUpdateDataType {
  return {
    tipo: 'PJ',
    razao_social: formData.razao_social || undefined,
    nome_fantasia: formData.nome_fantasia || undefined,
    cnpj: unmaskDocument(formData.cnpj || '') || undefined,
    ie: formData.ie || undefined,
    im: formData.im || undefined,
    regime_tributario: formData.regime_tributario || undefined,
    responsavel: formData.responsavel || undefined,
    email: formData.email || undefined,
    celular: unmaskPhone(formData.celular || '') || undefined,
    telefone: unmaskPhone(formData.telefone || '') || undefined,
    observacoes: formData.observacoes || undefined,
    endereco: prepareAddresses(formData.enderecos || [], true),
  };
}
