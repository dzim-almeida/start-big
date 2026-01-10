/**
 * @fileoverview Composables para formulários do onboarding
 * @description Gerencia os formulários de empresa, endereço e confirmação
 * de cadastro usando vee-validate e vue-query.
 */

import { ref, watch } from 'vue';
import { useForm } from 'vee-validate';
import { useOnboarding } from './useOnboarding';
import {
  AddressFormData,
  addressValidationSchema,
  CompanyFormData,
  companyValidationSchema,
} from '../schemas/onboarding.schema';
import type { CreateCompanyRequest, CreateCompanyResponse, DocumentType } from '../types/onboarding.types';
import { useCepQuery } from './useCepLookup';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useMutation } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { createCompany } from '../services/onboarding.service';
import { useToast } from '@/shared/composables/useToast';
import { unmaskCep, unmaskDocument, unmaskPhone } from '@/shared/utils/unmask.utils';
import { useAppNavigation } from '@/shared/composables/useAppNavigation';

/* ============================================
   useCompanyForm
   ============================================ */

/**
 * Composable para gerenciar o formulário de dados da empresa (Step 2)
 * @returns Campos do formulário, erros e métodos de manipulação
 */
export function useCompanyForm() {
  const {
    onboardingData,
    nextStep,
    updateCompanyData,
    updateContactData,
    setDocumentType,
  } = useOnboarding();

  /* ============================================
     Form Configuration
     ============================================ */

  /**
   * Configuração do formulário com vee-validate
   */
  const { handleSubmit, errors, defineField, submitCount, setFieldValue } =
    useForm<CompanyFormData>({
      validationSchema: companyValidationSchema,
      initialValues: {
        razaoSocial: onboardingData.company.razaoSocial,
        nomeFantasia: onboardingData.company.nomeFantasia,
        tipoDocumento: onboardingData.company.tipoDocumento,
        documento: onboardingData.company.documento,
        celular: onboardingData.contact.celular,
        email: onboardingData.contact.email,
        telefone: onboardingData.contact.telefone,
      },
    });

  /* ============================================
     Field Definitions
     ============================================ */

  const [razaoSocial] = defineField('razaoSocial');
  const [nomeFantasia] = defineField('nomeFantasia');
  const [tipoDocumento] = defineField('tipoDocumento');
  const [documento] = defineField('documento');
  const [celular] = defineField('celular');
  const [email] = defineField('email');
  const [telefone] = defineField('telefone');

  /* ============================================
     Handlers
     ============================================ */

  /**
   * Handler de submit do formulário
   * Atualiza os dados no estado global e avança para próxima etapa
   */
  const onSubmit = handleSubmit((formData) => {
    updateCompanyData({
      razaoSocial: formData.razaoSocial,
      nomeFantasia: formData.nomeFantasia,
      tipoDocumento: formData.tipoDocumento,
      documento: formData.documento,
    });

    updateContactData({
      celular: formData.celular,
      email: formData.email,
      telefone: formData.telefone || '',
    });

    nextStep();
  });

  /**
   * Handler para mudança de tipo de documento (CNPJ/CPF)
   * @param {DocumentType} type - Novo tipo de documento
   */
  function handleDocumentTypeChange(type: DocumentType): void {
    setFieldValue('tipoDocumento', type);
    setFieldValue('documento', '');
    setDocumentType(type);
  }

  return {
    // Campos do formulário
    razaoSocial,
    nomeFantasia,
    tipoDocumento,
    documento,
    celular,
    email,
    telefone,

    // Erros
    errors,

    // Métodos
    onSubmit,
    submitCount,
    handleDocumentTypeChange,
  };
}

/* ============================================
   useAddressForm
   ============================================ */

/**
 * Composable para gerenciar o formulário de endereço (Step 3)
 * @returns Campos do formulário, estados de loading e métodos
 */
export function useAddressForm() {
  const { onboardingData, nextStep, updateAddressData } = useOnboarding();

  /* ============================================
     Form Configuration
     ============================================ */

  /**
   * Configuração do formulário com vee-validate
   */
  const { handleSubmit, errors, defineField, submitCount, setValues } =
    useForm<AddressFormData>({
      validationSchema: addressValidationSchema,
      initialValues: {
        cep: onboardingData.address.cep,
        logradouro: onboardingData.address.logradouro,
        numero: onboardingData.address.numero,
        complemento: onboardingData.address.complemento,
        bairro: onboardingData.address.bairro,
        cidade: onboardingData.address.cidade,
        estado: onboardingData.address.estado,
      },
    });

  /* ============================================
     Field Definitions
     ============================================ */

  const [cep] = defineField('cep');
  const [logradouro] = defineField('logradouro');
  const [numero] = defineField('numero');
  const [complemento] = defineField('complemento');
  const [bairro] = defineField('bairro');
  const [cidade] = defineField('cidade');
  const [estado] = defineField('estado');

  /* ============================================
     CEP Query
     ============================================ */

  /**
   * Query para busca automática de endereço por CEP
   */
  const { data: cepData, isLoading: cepIsLoading, isError: cepIsError } = useCepQuery(cep);

  /* ============================================
     Watchers
     ============================================ */

  /**
   * Watch para preenchimento automático ao buscar CEP
   */
  watch(cepData, (data) => {
    if (data) {
      setValues({
        cep: cep.value,
        logradouro: data.logradouro || '',
        bairro: data.bairro || '',
        cidade: data.localidade || '',
        estado: data.uf || '',
        numero: '',
        complemento: data.complemento || '',
      });
    }
  });

  /* ============================================
     Handlers
     ============================================ */

  /**
   * Handler de submit do formulário
   * Atualiza os dados no estado global e avança para próxima etapa
   */
  const onSubmit = handleSubmit((formData) => {
    updateAddressData({
      cep: formData.cep,
      logradouro: formData.logradouro,
      numero: formData.numero,
      complemento: formData.complemento || '',
      bairro: formData.bairro,
      cidade: formData.cidade,
      estado: formData.estado,
    });

    nextStep();
  });

  return {
    // Campos do formulário
    cep,
    logradouro,
    numero,
    complemento,
    bairro,
    cidade,
    estado,

    // Estados
    errors,
    cepIsLoading,
    cepIsError,

    // Métodos
    onSubmit,
    submitCount,
  };
}

/* ============================================
   useConfirmRegisterEmpresa
   ============================================ */

/**
 * Composable para gerenciar a confirmação e envio do cadastro (Step 4)
 * @returns Estado de loading, erro e método de confirmação
 */
export function useConfirmRegisterEmpresa() {
  const { goToHome } = useAppNavigation();
  const toast = useToast();
  const { onboardingData, resetOnboarding } = useOnboarding();

  /* ============================================
     State
     ============================================ */

  /** Mensagem de erro da API */
  const apiError = ref<string | null>(null);

  /* ============================================
     Mutation
     ============================================ */

  /**
   * Mutation para criar empresa via API
   */
  const createCompanyMutation = useMutation<
    CreateCompanyResponse,
    AxiosError<ApiError>,
    CreateCompanyRequest
  >({
    mutationFn: createCompany,
    onSuccess: () => {
      toast.success(
        'Empresa cadastrada com sucesso!',
        'Sua configuração inicial foi concluída. Bem-vindo ao Start Big!'
      );
      resetOnboarding();
      goToHome();
    },
    onError: (error) => {
      apiError.value = getErrorMessage(error, 'Erro ao cadastrar empresa');
    },
  });

  /* ============================================
     Handlers
     ============================================ */

  /**
   * Confirma e envia os dados para criação da empresa
   * Valida se o segmento foi selecionado antes de enviar
   */
  function confirmSubmit(): void {
    if (!onboardingData.company.segmento) return;

    apiError.value = null;

    const request: CreateCompanyRequest = {
      razao_social: onboardingData.company.razaoSocial,
      nome_fantasia: onboardingData.company.nomeFantasia,
      tipo_documento: onboardingData.company.tipoDocumento,
      is_cnpj: onboardingData.company.tipoDocumento === 'CNPJ',
      documento: unmaskDocument(onboardingData.company.documento),
      segmento: onboardingData.company.segmento,
      celular: unmaskPhone(onboardingData.contact.celular),
      email: onboardingData.contact.email,
      telefone: onboardingData.contact.telefone
        ? unmaskPhone(onboardingData.contact.telefone)
        : undefined,
      endereco: [
        {
          cep: unmaskCep(onboardingData.address.cep),
          logradouro: onboardingData.address.logradouro,
          numero: onboardingData.address.numero,
          complemento: onboardingData.address.complemento || undefined,
          bairro: onboardingData.address.bairro,
          cidade: onboardingData.address.cidade,
          estado: onboardingData.address.estado,
        }
      ]
    };

    createCompanyMutation.mutate(request);
  }

  return {
    // Estados (mantendo reatividade)
    isPending: createCompanyMutation.isPending,
    apiError,

    // Métodos
    confirmSubmit,
  };
}
