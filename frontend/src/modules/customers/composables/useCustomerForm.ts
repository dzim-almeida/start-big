/**
 * @fileoverview Customer form composable with provide/inject pattern
 * @description Manages form state, validation, and submission for create/edit
 * Supports both PF (individual) and PJ (company) customer types
 * Uses provide/inject to share form state between components
 */

import {
  ref,
  watch,
  computed,
  provide,
  inject,
  type InjectionKey,
  type Ref,
  type ComputedRef,
} from 'vue';
import { useForm, useFieldArray, type FieldEntry } from 'vee-validate';
import {
  customerPFValidationSchema,
  customerPJValidationSchema,
  type AddressFormData,
} from '../schemas/customer.schema';
import type {
  Cliente,
  ClientePFCreate,
  ClientePJCreate,
  ClientePFUpdate,
  ClientePJUpdate,
  TipoCliente,
  Gender,
  State,
} from '../types/clientes.types';
import { useCustomerModal } from './useCustomerModal';
import { useClienteActions } from '@/shared/composables/cliente/useClienteActions';
import { unmaskDocument, unmaskPhone, unmaskCep } from '@/shared/utils/unmask.utils';

// =============================================
// Constants
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
  enderecos: [{...DEFAULT_ADDRESS}] as AddressFormData[],
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
  enderecos: [{...DEFAULT_ADDRESS}] as AddressFormData[],
};

export const CUSTOMER_TYPE_TABS = [
  { id: 'PF', label: 'Pessoa Física' },
  { id: 'PJ', label: 'Pessoa Jurídica' },
];

export const GENDER_OPTIONS = [
  { value: 'MASCULINO', label: 'Masculino' },
  { value: 'FEMININO', label: 'Feminino' },
  { value: 'OUTRO', label: 'Outro' },
];

// =============================================
// Types for Injection
// =============================================

export interface CustomerFormContext {
  // Customer type
  customerType: Ref<TipoCliente>;
  setCustomerType: (type: TipoCliente) => void;

  // PF Fields
  nome: Ref<string>;
  cpf: Ref<string>;
  rg: Ref<string>;
  genero: Ref<string>;
  data_nascimento: Ref<string>;

  // PJ Fields
  razao_social: Ref<string>;
  nome_fantasia: Ref<string>;
  cnpj: Ref<string>;
  ie: Ref<string>;
  im: Ref<string>;
  regime_tributario: Ref<string>;
  responsavel: Ref<string>;

  // Common Fields
  email: Ref<string>;
  celular: Ref<string>;
  telefone: Ref<string>;
  observacoes: Ref<string>;

  // Addresses
  enderecos: Ref<FieldEntry<AddressFormData>[]>;
  handleAddAddress: () => void;
  handleRemoveAddress: (index: number) => void;

  // Form state
  errors: Ref<Record<string, string | undefined>>;
  submitCount: Ref<number>;
  apiError: Ref<string | null>;
  isPending: ComputedRef<boolean>;

  // Actions
  onSubmit: (e?: Event) => void;
  resetForm: () => void;
}

// Injection key for type safety
export const CUSTOMER_FORM_KEY: InjectionKey<CustomerFormContext> = Symbol('customer-form');

// =============================================
// Helper Functions
// =============================================

function prepareAddresses(addresses: AddressFormData[], isUpdate: boolean) {
  if (addresses.length === 0) return undefined;

  return addresses.map((addr) => ({
    ...(isUpdate && addr.id ? { id: addr.id } : {}),
    cep: unmaskCep(addr.cep),
    logradouro: addr.logradouro,
    numero: addr.numero,
    complemento: addr.complemento || undefined,
    bairro: addr.bairro,
    cidade: addr.cidade,
    estado: addr.estado as State,
  }));
}

// =============================================
// Provider Composable (call in modal component)
// =============================================

export function useCustomerFormProvider() {
  const { selectedCustomer, isCreateMode, closeModal } = useCustomerModal();
  const { createPFMutation, createPJMutation, updateMutation } = useClienteActions();

  // Customer type state
  const customerType = ref<TipoCliente>('PF');

  // Initialize PF form
  const pfForm = useForm({
    validationSchema: customerPFValidationSchema,
    initialValues: { ...DEFAULT_PF_VALUES },
  });

  // Initialize PJ form
  const pjForm = useForm({
    validationSchema: customerPJValidationSchema,
    initialValues: { ...DEFAULT_PJ_VALUES },
  });

  // Get active form based on customer type
  const getActiveForm = () => (customerType.value === 'PF' ? pfForm : pjForm);

  // Define PF fields
  const [nome] = pfForm.defineField('nome');
  const [cpf] = pfForm.defineField('cpf');
  const [rg] = pfForm.defineField('rg');
  const [genero] = pfForm.defineField('genero');
  const [data_nascimento] = pfForm.defineField('data_nascimento');
  const [pfEmail] = pfForm.defineField('email');
  const [pfCelular] = pfForm.defineField('celular');
  const [pfTelefone] = pfForm.defineField('telefone');
  const [pfObservacoes] = pfForm.defineField('observacoes');

  // Define PJ fields
  const [razao_social] = pjForm.defineField('razao_social');
  const [nome_fantasia] = pjForm.defineField('nome_fantasia');
  const [cnpj] = pjForm.defineField('cnpj');
  const [ie] = pjForm.defineField('ie');
  const [im] = pjForm.defineField('im');
  const [regime_tributario] = pjForm.defineField('regime_tributario');
  const [responsavel] = pjForm.defineField('responsavel');
  const [pjEmail] = pjForm.defineField('email');
  const [pjCelular] = pjForm.defineField('celular');
  const [pjTelefone] = pjForm.defineField('telefone');
  const [pjObservacoes] = pjForm.defineField('observacoes');

  // Field arrays for addresses
  const pfAddresses = useFieldArray<AddressFormData>('enderecos');
  const pjAddresses = useFieldArray<AddressFormData>('enderecos');

  // Computed refs that switch based on customer type
  const email = computed({
    get: () => (customerType.value === 'PF' ? pfEmail.value : pjEmail.value),
    set: (val) => {
      if (customerType.value === 'PF') pfEmail.value = val;
      else pjEmail.value = val;
    },
  });

  const celular = computed({
    get: () => (customerType.value === 'PF' ? pfCelular.value : pjCelular.value),
    set: (val) => {
      if (customerType.value === 'PF') pfCelular.value = val;
      else pjCelular.value = val;
    },
  });

  const telefone = computed({
    get: () => (customerType.value === 'PF' ? pfTelefone.value : pjTelefone.value),
    set: (val) => {
      if (customerType.value === 'PF') pfTelefone.value = val;
      else pjTelefone.value = val;
    },
  });

  const observacoes = computed({
    get: () => (customerType.value === 'PF' ? pfObservacoes.value : pjObservacoes.value),
    set: (val) => {
      if (customerType.value === 'PF') pfObservacoes.value = val;
      else pjObservacoes.value = val;
    },
  });

  const enderecos = computed(() =>
    customerType.value === 'PF' ? pfAddresses.fields.value : pjAddresses.fields.value
  );

  const errors = computed(() =>
    customerType.value === 'PF' ? pfForm.errors.value : pjForm.errors.value
  );

  const submitCount = computed(() =>
    customerType.value === 'PF' ? pfForm.submitCount.value : pjForm.submitCount.value
  );

  const apiError = ref<string | null>(null);

  // Address handlers
  function handleAddAddress() {
    if (customerType.value === 'PF') {
      pfAddresses.push({ ...DEFAULT_ADDRESS });
    } else {
      pjAddresses.push({ ...DEFAULT_ADDRESS });
    }
  }

  function handleRemoveAddress(index: number) {
    if (customerType.value === 'PF') {
      pfAddresses.remove(index);
    } else {
      pjAddresses.remove(index);
    }
  }

  // Set customer type
  function setCustomerType(type: TipoCliente) {
    customerType.value = type;
  }

  // Populate form when editing
  function populateForm(customer: Cliente) {
    customerType.value = customer.tipo;

    const addresses = customer.endereco?.map((end) => ({
      id: end.id,
      cep: end.cep || '',
      logradouro: end.logradouro || '',
      numero: end.numero || '',
      complemento: end.complemento || '',
      bairro: end.bairro || '',
      cidade: end.cidade || '',
      estado: end.estado || '',
    })) || [];

    if (customer.tipo === 'PF') {
      pfForm.setValues({
        nome: customer.nome,
        cpf: customer.cpf || '',
        rg: customer.rg || '',
        genero: customer.genero || '',
        data_nascimento: customer.data_nascimento || '',
        email: customer.email || '',
        celular: customer.celular || '',
        telefone: customer.telefone || '',
        observacoes: customer.observacoes || '',
        enderecos: addresses,
      });
    } else {
      pjForm.setValues({
        razao_social: customer.razao_social,
        nome_fantasia: customer.nome_fantasia || '',
        cnpj: customer.cnpj || '',
        ie: customer.ie || '',
        im: customer.im || '',
        regime_tributario: customer.regime_tributario || '',
        responsavel: customer.responsavel || '',
        email: customer.email || '',
        celular: customer.celular || '',
        telefone: customer.telefone || '',
        observacoes: customer.observacoes || '',
        enderecos: addresses,
      });
    }
  }

  // Watch for customer changes
  watch(
    selectedCustomer,
    (customer) => {
      if (customer) {
        populateForm(customer);
      } else {
        pfForm.resetForm({ values: { ...DEFAULT_PF_VALUES } });
        pjForm.resetForm({ values: { ...DEFAULT_PJ_VALUES } });
        customerType.value = 'PF';
      }
    },
    { immediate: true }
  );

  // Transform PF data for API
  function transformPFToCreateRequest(): ClientePFCreate {
    const formData = pfForm.values;
    return {
      tipo: 'PF',
      nome: formData.nome,
      cpf: unmaskDocument(formData.cpf) || undefined,
      rg: formData.rg || undefined,
      genero: (formData.genero as Gender) || undefined,
      data_nascimento: formData.data_nascimento || undefined,
      email: formData.email || undefined,
      celular: unmaskPhone(formData.celular) || undefined,
      telefone: unmaskPhone(formData.telefone) || undefined,
      observacoes: formData.observacoes || undefined,
      endereco: prepareAddresses(formData.enderecos, false),
    };
  }

  // Transform PJ data for API
  function transformPJToCreateRequest(): ClientePJCreate {
    const formData = pjForm.values;
    return {
      razao_social: formData.razao_social,
      nome_fantasia: formData.nome_fantasia || undefined,
      cnpj: unmaskDocument(formData.cnpj) || undefined,
      ie: formData.ie || undefined,
      im: formData.im || undefined,
      regime_tributario: formData.regime_tributario || undefined,
      responsavel: formData.responsavel || undefined,
      email: formData.email || undefined,
      celular: unmaskPhone(formData.celular) || undefined,
      telefone: unmaskPhone(formData.telefone) || undefined,
      observacoes: formData.observacoes || undefined,
      endereco: prepareAddresses(formData.enderecos, false),
    };
  }

  // Transform PF data for update
  function transformPFToUpdateRequest(): ClientePFUpdate {
    const formData = pfForm.values;
    return {
      tipo: 'PF',
      nome: formData.nome,
      cpf: unmaskDocument(formData.cpf) || undefined,
      rg: formData.rg || undefined,
      genero: (formData.genero as Gender) || undefined,
      data_nascimento: formData.data_nascimento || undefined,
      email: formData.email || undefined,
      celular: unmaskPhone(formData.celular) || undefined,
      telefone: unmaskPhone(formData.telefone) || undefined,
      observacoes: formData.observacoes || undefined,
      endereco: prepareAddresses(formData.enderecos, true),
    };
  }

  // Transform PJ data for update
  function transformPJToUpdateRequest(): ClientePJUpdate {
    const formData = pjForm.values;
    return {
      tipo: 'PJ',
      razao_social: formData.razao_social,
      nome_fantasia: formData.nome_fantasia || undefined,
      cnpj: unmaskDocument(formData.cnpj) || undefined,
      ie: formData.ie || undefined,
      im: formData.im || undefined,
      regime_tributario: formData.regime_tributario || undefined,
      responsavel: formData.responsavel || undefined,
      email: formData.email || undefined,
      celular: unmaskPhone(formData.celular) || undefined,
      telefone: unmaskPhone(formData.telefone) || undefined,
      observacoes: formData.observacoes || undefined,
      endereco: prepareAddresses(formData.enderecos, true),
    };
  }

  // Submit handler
  const onSubmit = async (e?: Event) => {
    e?.preventDefault();
    apiError.value = null;

    const activeForm = getActiveForm();
    const { valid } = await activeForm.validate();

    if (!valid) {
      return;
    }

    try {
      if (isCreateMode.value) {
        if (customerType.value === 'PF') {
          const request = transformPFToCreateRequest();
          await createPFMutation.mutateAsync(request);
        } else {
          const request = transformPJToCreateRequest();
          await createPJMutation.mutateAsync(request);
        }
      } else if (selectedCustomer.value) {
        if (customerType.value === 'PF') {
          const request = transformPFToUpdateRequest();
          await updateMutation.mutateAsync({
            id: selectedCustomer.value.id,
            data: request,
          });
        } else {
          const request = transformPJToUpdateRequest();
          await updateMutation.mutateAsync({
            id: selectedCustomer.value.id,
            data: request,
          });
        }
      }

      closeModal();
      pfForm.resetForm({ values: { ...DEFAULT_PF_VALUES } });
      pjForm.resetForm({ values: { ...DEFAULT_PJ_VALUES } });
    } catch (error: any) {
      apiError.value = error?.response?.data?.detail || 'Erro ao salvar cliente';
    }
  };

  const isPending = computed(
    () =>
      createPFMutation.isPending.value ||
      createPJMutation.isPending.value ||
      updateMutation.isPending.value
  );

  // Reset form function
  function resetForm() {
    pfForm.resetForm({ values: { ...DEFAULT_PF_VALUES } });
    pjForm.resetForm({ values: { ...DEFAULT_PJ_VALUES } });
    customerType.value = 'PF';
    apiError.value = null;
  }

  // Create context object
  const context: CustomerFormContext = {
    // Customer type
    customerType,
    setCustomerType,

    // PF Fields
    nome,
    cpf,
    rg,
    genero,
    data_nascimento,

    // PJ Fields
    razao_social,
    nome_fantasia,
    cnpj,
    ie,
    im,
    regime_tributario,
    responsavel,

    // Common Fields (computed refs)
    email: email as unknown as Ref<string>,
    celular: celular as unknown as Ref<string>,
    telefone: telefone as unknown as Ref<string>,
    observacoes: observacoes as unknown as Ref<string>,

    // Addresses
    enderecos: enderecos as unknown as Ref<FieldEntry<AddressFormData>[]>,
    handleAddAddress,
    handleRemoveAddress,

    // Form state
    errors: errors as unknown as Ref<Record<string, string | undefined>>,
    submitCount: submitCount as unknown as Ref<number>,
    apiError,
    isPending,

    // Actions
    onSubmit,
    resetForm,
  };

  // Provide context to children
  provide(CUSTOMER_FORM_KEY, context);

  return context;
}

// =============================================
// Consumer Composable (call in child components)
// =============================================

export function useCustomerForm(): CustomerFormContext {
  const context = inject(CUSTOMER_FORM_KEY);

  if (!context) {
    throw new Error(
      'useCustomerForm must be used within a component that has called useCustomerFormProvider'
    );
  }

  return context;
}
