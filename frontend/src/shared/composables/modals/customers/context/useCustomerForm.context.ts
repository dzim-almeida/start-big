import {
  ref,
  watch,
  computed,
  provide,
  inject,
  type InjectionKey,
  type Ref,
} from 'vue';
import type { FieldEntry } from 'vee-validate';

import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import type { TipoCliente } from '@/modules/customers/types/clientes.types';
import type { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';

import type { CustomerFormContext } from '../types/context.type';
import { useCustomerPFForm } from '../form/useCustomerPF.form';
import { useCustomerPJForm } from '../form/useCustomerPJ.form';
import { DEFAULT_PF_VALUES, DEFAULT_PJ_VALUES } from '../constants/customer.constant';
import {
  transformPFToCreateRequest,
  transformPJToCreateRequest,
  transformPFToUpdateRequest,
  transformPJToUpdateRequest,
} from '../form/helpers/transform.helpers';

import { useCustomerModal } from '../useCustomerModal';
import { useClienteActions } from '@/shared/composables/cliente/useClienteActions';

// =============================================
// Injection Key
// =============================================

export const CUSTOMER_FORM_KEY: InjectionKey<CustomerFormContext> = Symbol('customer-form');

// =============================================
// Provider (chamado no CustomerFormModal)
// =============================================

export function useCustomerFormProvider(): CustomerFormContext {
  const { selectedCustomer, isCreateMode, closeModal } = useCustomerModal();
  const { createPFMutation, createPJMutation, updateMutation } = useClienteActions();

  const customerType = ref<TipoCliente>('PF');
  const apiError = ref<string | null>(null);

  // Instanciar formulários PF e PJ
  const pfForm = useCustomerPFForm();
  const pjForm = useCustomerPJForm();

  // Computed switching refs para campos comuns
  const email = computed({
    get: () => (customerType.value === 'PF' ? pfForm.email.value : pjForm.email.value),
    set: (val) => {
      if (customerType.value === 'PF') pfForm.email.value = val;
      else pjForm.email.value = val;
    },
  });

  const celular = computed({
    get: () => (customerType.value === 'PF' ? pfForm.celular.value : pjForm.celular.value),
    set: (val) => {
      if (customerType.value === 'PF') pfForm.celular.value = val;
      else pjForm.celular.value = val;
    },
  });

  const telefone = computed({
    get: () => (customerType.value === 'PF' ? pfForm.telefone.value : pjForm.telefone.value),
    set: (val) => {
      if (customerType.value === 'PF') pfForm.telefone.value = val;
      else pjForm.telefone.value = val;
    },
  });

  const observacoes = computed({
    get: () => (customerType.value === 'PF' ? pfForm.observacoes.value : pjForm.observacoes.value),
    set: (val) => {
      if (customerType.value === 'PF') pfForm.observacoes.value = val;
      else pjForm.observacoes.value = val;
    },
  });

  const enderecos = computed(() =>
    customerType.value === 'PF' ? pfForm.enderecos.value : pjForm.enderecos.value,
  );

  const errors = computed(() =>
    customerType.value === 'PF' ? pfForm.errors.value : pjForm.errors.value,
  );

  const submitCount = computed(() =>
    customerType.value === 'PF' ? pfForm.submitCount.value : pjForm.submitCount.value,
  );

  // ── Handlers ─────────────────────────────────

  function setCustomerType(type: TipoCliente) {
    customerType.value = type;
  }

  function handleAddAddress() {
    if (customerType.value === 'PF') pfForm.handleAddAddress();
    else pjForm.handleAddAddress();
  }

  function handleRemoveAddress(index: number) {
    if (customerType.value === 'PF') pfForm.handleRemoveAddress(index);
    else pjForm.handleRemoveAddress(index);
  }

  // ── Populate ao editar ───────────────────────

  function populateForm(customer: CustomerUnionReadSchemaDataType) {
    customerType.value = customer.tipo as TipoCliente;

    const addresses = (customer as any).endereco?.map((end: any) => ({
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
      const pf = customer as any;
      pfForm.setValues({
        nome: pf.nome,
        cpf: pf.cpf || '',
        rg: pf.rg || '',
        genero: pf.genero || '',
        data_nascimento: pf.data_nascimento || '',
        email: pf.email || '',
        celular: pf.celular || '',
        telefone: pf.telefone || '',
        observacoes: pf.observacoes || '',
        enderecos: addresses,
      });
    } else {
      const pj = customer as any;
      pjForm.setValues({
        razao_social: pj.razao_social,
        nome_fantasia: pj.nome_fantasia || '',
        cnpj: pj.cnpj || '',
        ie: pj.ie || '',
        im: pj.im || '',
        regime_tributario: pj.regime_tributario || '',
        responsavel: pj.responsavel || '',
        email: pj.email || '',
        celular: pj.celular || '',
        telefone: pj.telefone || '',
        observacoes: pj.observacoes || '',
        enderecos: addresses,
      });
    }
  }

  // ── Watch selectedCustomer → populate/reset ──

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
    { immediate: true },
  );

  // ── Submit ───────────────────────────────────

  const onSubmit = async () => {
    apiError.value = null;

    const activeForm = customerType.value === 'PF' ? pfForm : pjForm;
    const { valid } = await activeForm.validate();

    if (!valid) return;

    try {
      if (isCreateMode.value) {
        if (customerType.value === 'PF') {
          await createPFMutation.mutateAsync(transformPFToCreateRequest(pfForm.values));
        } else {
          await createPJMutation.mutateAsync(transformPJToCreateRequest(pjForm.values));
        }
      } else if (selectedCustomer.value) {
        const id = (selectedCustomer.value as any).id;
        if (customerType.value === 'PF') {
          await updateMutation.mutateAsync({ id, data: transformPFToUpdateRequest(pfForm.values) });
        } else {
          await updateMutation.mutateAsync({ id, data: transformPJToUpdateRequest(pjForm.values) });
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
      updateMutation.isPending.value,
  );

  function resetForm() {
    pfForm.resetForm({ values: { ...DEFAULT_PF_VALUES } });
    pjForm.resetForm({ values: { ...DEFAULT_PJ_VALUES } });
    customerType.value = 'PF';
    apiError.value = null;
  }

  // ── Montar contexto ──────────────────────────

  const context: CustomerFormContext = {
    customerType,
    setCustomerType,

    // PF
    nome: pfForm.nome,
    cpf: pfForm.cpf,
    rg: pfForm.rg,
    genero: pfForm.genero,
    data_nascimento: pfForm.data_nascimento,

    // PJ
    razao_social: pjForm.razao_social,
    nome_fantasia: pjForm.nome_fantasia,
    cnpj: pjForm.cnpj,
    ie: pjForm.ie,
    im: pjForm.im,
    regime_tributario: pjForm.regime_tributario,
    responsavel: pjForm.responsavel,

    // Comuns (computed)
    email: email as unknown as Ref<string>,
    celular: celular as unknown as Ref<string>,
    telefone: telefone as unknown as Ref<string>,
    observacoes: observacoes as unknown as Ref<string>,

    // Endereços
    enderecos: enderecos as unknown as Ref<FieldEntry<AddressFormData>[]>,
    handleAddAddress,
    handleRemoveAddress,

    // Estado
    errors: errors as unknown as Ref<Record<string, string | undefined>>,
    submitCount: submitCount as unknown as Ref<number>,
    apiError,
    isPending,

    // Ações
    onSubmit,
    resetForm,
  };

  provide(CUSTOMER_FORM_KEY, context);

  return context;
}

// =============================================
// Consumer (chamado nos child components)
// =============================================

export function useCustomerForm(): CustomerFormContext {
  const context = inject(CUSTOMER_FORM_KEY);

  if (!context) {
    throw new Error(
      'useCustomerForm deve ser usado dentro de um componente que chamou useCustomerFormProvider',
    );
  }

  return context;
}
