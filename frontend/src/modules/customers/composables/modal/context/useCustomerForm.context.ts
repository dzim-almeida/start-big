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
import { DEFAULT_PF_VALUES, DEFAULT_PJ_VALUES } from '../constants/modal.constant';
import {
  transformPFToCreateRequest,
  transformPJToCreateRequest,
  transformPFToUpdateRequest,
  transformPJToUpdateRequest,
} from '../form/helpers/transform.helpers';

import type { AxiosError } from 'axios';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage, getConflictErrors, isConflictError } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';

import { useCustomerModal } from '../useCustomerModal';
import { useCreateCustomerPFMutation, useCreateCustomerPJMutation } from '@/modules/customers/composables/request/useCustomerCreate.mutate';
import { useUpdateCustomerMutation } from '@/modules/customers/composables/request/useCustomerUpdate.mutate';

// =============================================
// Injection Key
// =============================================

export const CUSTOMER_FORM_KEY: InjectionKey<CustomerFormContext> = Symbol('customer-form');

// =============================================
// Provider (chamado no CustomerFormModal)
// =============================================

export function useCustomerFormProvider(): CustomerFormContext {
  const { selectedCustomer, isCreateMode, closeModal, onCreatedCallback, onUpdatedCallback } = useCustomerModal();
  const createPFMutation = useCreateCustomerPFMutation();
  const createPJMutation = useCreateCustomerPJMutation();
  const updateMutation = useUpdateCustomerMutation();

  const toast = useToast();
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
        apiError.value = null;
      }
    },
    { immediate: true },
  );

  // ── Error handling ─────────────────────────────

  function handleApiError(error: AxiosError<ApiError>, setErrors: (errors: Record<string, string>) => void, defaultMessage: string) {
    if (isConflictError(error)) {
      const conflictErrors = getConflictErrors(error);
      if (conflictErrors) {
        setErrors(conflictErrors);
        toast.error('Dados já registrados', getErrorMessage(error, defaultMessage));
        return;
      }
    }
    apiError.value = getErrorMessage(error, defaultMessage);
    toast.error(apiError.value);
  }

  // ── Submit ───────────────────────────────────

  const pfSubmit = pfForm.handleSubmit(async (data) => {
    apiError.value = null;

    try {
      if (isCreateMode.value) {
        const created = await createPFMutation.mutateAsync(transformPFToCreateRequest(data));
        onCreatedCallback.value?.(created);
      } else if (selectedCustomer.value) {
        const id = selectedCustomer.value.id;
        const updated = await updateMutation.mutateAsync({ id, data: transformPFToUpdateRequest(data) });
        onUpdatedCallback.value?.(updated);
      }
      closeModal();
      pfForm.resetForm({ values: { ...DEFAULT_PF_VALUES } });
    } catch (error) {
      handleApiError(error as AxiosError<ApiError>, pfForm.setErrors, 'Erro ao salvar cliente PF');
    }
  });

  const pjSubmit = pjForm.handleSubmit(async (data) => {
    apiError.value = null;

    try {
      if (isCreateMode.value) {
        const created = await createPJMutation.mutateAsync(transformPJToCreateRequest(data));
        onCreatedCallback.value?.(created);
      } else if (selectedCustomer.value) {
        const id = selectedCustomer.value.id;
        const updated = await updateMutation.mutateAsync({ id, data: transformPJToUpdateRequest(data) });
        onUpdatedCallback.value?.(updated);
      }
      closeModal();
      pjForm.resetForm({ values: { ...DEFAULT_PJ_VALUES } });
    } catch (error) {
      handleApiError(error as AxiosError<ApiError>, pjForm.setErrors, 'Erro ao salvar cliente PJ');
    }
  });

  const onSubmit = async () => {
    apiError.value = null;

    if (customerType.value === 'PF') {
      await pfSubmit();
    } else {
      await pjSubmit();
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
