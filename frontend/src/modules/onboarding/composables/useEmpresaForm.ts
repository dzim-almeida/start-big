import { ref, watch } from 'vue';
import { useForm } from 'vee-validate';
import { useOnboarding } from './useOnboarding';
import {
  AddressFormData,
  addressValidationSchema,
  CompanyFormData,
  companyValidationSchema,
} from '../schemas/onboarding.schema';
import { CreateCompanyRequest, CreateCompanyResponse, DocumentType } from '../types/onboarding.types';
import { useCepQuery } from './useCepLookup';
import { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useMutation } from '@tanstack/vue-query';
import { AxiosError } from 'axios';
import { createCompany } from '../services/onboarding.service';
import { useToast } from '@/shared/composables/useToast';
import { useRouter } from 'vue-router';
import { unmaskCep, unmaskDocument, unmaskPhone } from '@/shared/utils/unmask.utils';

const {
  onboardingData,
  nextStep,
  updateCompanyData,
  updateContactData,
  updateAddressData,
  setDocumentType,
  resetOnboarding
} = useOnboarding();

// Formulário com dados da empresa
export function useCompanyForm() {
  /**
   * Configuração do formulário
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

  /**
   * Definição dos campos
   */
  const [razaoSocial] = defineField('razaoSocial');
  const [nomeFantasia] = defineField('nomeFantasia');
  const [tipoDocumento] = defineField('tipoDocumento');
  const [documento] = defineField('documento');
  const [celular] = defineField('celular');
  const [email] = defineField('email');
  const [telefone] = defineField('telefone');

  /**
   * Handler de submit
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
   * Handler para mudança de tipo de documento
   */
  function handleDocumentTypeChange(type: DocumentType) {
    setFieldValue('tipoDocumento', type);
    setFieldValue('documento', '');
    setDocumentType(type);
  }

  return {
    //Campos do formulário
    razaoSocial,
    nomeFantasia,
    tipoDocumento,
    documento,
    celular,
    email,
    telefone,

    //Erros
    errors,

    //Métodos
    onSubmit,
    submitCount,
    handleDocumentTypeChange,
  };
}

export function useAddressForm() {
  /**
   * Configuração do formulário
   */
  const { handleSubmit, errors, defineField, submitCount, setValues } = useForm<AddressFormData>({
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

  /**
   * Definição dos campos
   */
  const [cep] = defineField('cep');
  const [logradouro] = defineField('logradouro');
  const [numero] = defineField('numero');
  const [complemento] = defineField('complemento');
  const [bairro] = defineField('bairro');
  const [cidade] = defineField('cidade');
  const [estado] = defineField('estado');

  /**
   * Handler de submit
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

  /**
   * Watch para busca automática de CEP
   */
  const { data: cepData, isLoading: cepIsLoading, isError: cepIsError } = useCepQuery(cep);

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

  /**
   * Busca automática do cep
   */
  return {
    //Campos do formulário
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

    //Métodos
    onSubmit,
    submitCount,
  };
}

export function useConfirmRegisterEmpresa() {
  const router = useRouter()
  const toast = useToast();
  const apiError = ref<string | null>(null);

  /**
   * Mutation para criar empresa
   */
  const createCompanyMutation = useMutation<CreateCompanyResponse, AxiosError<ApiError>, CreateCompanyRequest>({
    mutationFn: createCompany,
    onSuccess: () => {
      toast.success(
        'Empresa cadastrada com sucesso!',
        'Sua configuração inicial foi concluída. Bem-vindo ao Start Big!'
      );
      resetOnboarding();
      router.push('/');
    },
    onError: (error) => {
      apiError.value = getErrorMessage(error, 'Erro ao cadastrar empresa');
    },
  });

  function confirmSubmit() {
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
      telefone: onboardingData.contact.telefone ? unmaskPhone(onboardingData.contact.telefone) : undefined,
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
    // Estados
    isPending: createCompanyMutation.isPending.value,
    apiError,

    // Métodos
    confirmSubmit,
  }
}
