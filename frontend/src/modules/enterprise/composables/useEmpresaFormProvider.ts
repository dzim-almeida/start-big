import { ref, computed, watch, provide, inject, type InjectionKey } from 'vue';
import { useForm } from 'vee-validate';
import { empresaValidationSchema } from '../schemas/empresa.schema';
import {
  useEmpresaQuery,
  useUpdateEmpresaMutation,
  useUploadCertificadoMutation,
  useUploadLogoMutation,
  useTestSefazMutation,
  useTestPrefeituraMutation,
  useWindowsCertificatesQuery,
} from './useEmpresaQuery';
import { useAuthStore } from '@/shared/stores/auth.store';
import { DEFAULT_FISCAL_SETTINGS, DEFAULT_ENDERECO } from '../constants/empresa.constants';
import {
  formatCEP,
  formatCNPJ,
  formatCPF,
  formatTelefone,
  unmaskDocument,
  unmaskPhone,
  unmaskCep,
} from '@/shared/utils/document.utils';
import type {
  EmpresaFormData,
  EmpresaFormContext,
  EmpresaUpdate,
  Endereco,
} from '../types/empresa.types';

// =============================================
// Injection Key (type-safe)
// =============================================

export const EMPRESA_FORM_KEY: InjectionKey<EmpresaFormContext> = Symbol('empresa-form');

// =============================================
// Default Form Values
// =============================================

const DEFAULT_FORM_VALUES: EmpresaFormData = {
  razao_social: '',
  nome_fantasia: '',
  documento: '',
  is_cnpj: true,
  email: '',
  telefone: '',
  celular: '',
  inscricao_estadual: '',
  inscricao_municipal: '',
  regime_tributario: '',
  cnae_principal: '',
  url_logo: '',
  fiscal_settings: { ...DEFAULT_FISCAL_SETTINGS },
  endereco_principal: { ...DEFAULT_ENDERECO },
  certificado_senha: '',
};

// =============================================
// Funções utilitárias
// =============================================

function formatDocumento(documento: string, isCnpj: boolean | undefined): string {
  if (!documento) return '';
  const digits = documento.replace(/\D/g, '');
  if (isCnpj === true) return formatCNPJ(digits);
  if (isCnpj === false) return formatCPF(digits);
  if (digits.length === 14) return formatCNPJ(digits);
  if (digits.length === 11) return formatCPF(digits);
  return documento;
}

function normalizeEmpresaToForm(data: any): EmpresaFormData {
  const telefone = data.telefone ? formatTelefone(data.telefone) : '';
  const celular = data.celular ? formatTelefone(data.celular) : '';
  const enderecoPrincipal = data.enderecos?.[0];

  return {
    razao_social: data.razao_social ?? '',
    nome_fantasia: data.nome_fantasia ?? '',
    documento: formatDocumento(data.documento ?? '', data.is_cnpj),
    is_cnpj: data.is_cnpj ?? true,
    email: data.email ?? '',
    telefone,
    celular,
    inscricao_estadual: data.inscricao_estadual ?? '',
    inscricao_municipal: data.inscricao_municipal ?? '',
    regime_tributario: data.regime_tributario?.toString() ?? '',
    cnae_principal: data.cnae_principal ?? '',
    url_logo: data.url_logo ?? '',
    fiscal_settings: data.fiscal_settings ?? DEFAULT_FISCAL_SETTINGS,
    endereco_principal: enderecoPrincipal
      ? {
          ...enderecoPrincipal,
          cep: formatCEP(enderecoPrincipal.cep ?? ''),
        }
      : DEFAULT_ENDERECO,
    certificado_senha: '',
  };
}



// =============================================
// Provider Composable
// =============================================

/**
 * Provider de contexto do formulário de empresa
 * Gerencia estado com VeeValidate e provide/inject pattern
 *
 * @returns Context com fields, state, computed e actions
 */
export function useEmpresaFormProvider() {
  // Dependencies
  const authStore = useAuthStore();
  const empresaId = computed(() => authStore.userData?.empresa?.id);

  // TanStack Query hooks
  const { data: empresaData, isLoading } = useEmpresaQuery();

  const updateMutation = useUpdateEmpresaMutation();
  const uploadCertMutation = useUploadCertificadoMutation();
  const uploadLogoMutation = useUploadLogoMutation();
  const testSefazMutation = useTestSefazMutation();
  const testPrefeituraMutation = useTestPrefeituraMutation();
  const { data: windowsCertificates, refetch: refetchWindowsCerts } = useWindowsCertificatesQuery();

  // VeeValidate Form
  const { handleSubmit, errors, defineField, resetForm, submitCount, values, meta } =
    useForm<EmpresaFormData>({
      validationSchema: empresaValidationSchema,
      initialValues: { ...DEFAULT_FORM_VALUES },
    });

  // =============================================
  // Define Fields (VeeValidate)
  // =============================================

  const [razao_social] = defineField('razao_social');
  const [nome_fantasia] = defineField('nome_fantasia');
  const [documento] = defineField('documento');
  const [is_cnpj] = defineField('is_cnpj');
  const [email] = defineField('email');
  const [telefone] = defineField('telefone');
  const [celular] = defineField('celular');
  const [inscricao_estadual] = defineField('inscricao_estadual');
  const [inscricao_municipal] = defineField('inscricao_municipal');
  const [regime_tributario] = defineField('regime_tributario');
  const [cnae_principal] = defineField('cnae_principal');
  const [url_logo] = defineField('url_logo');
  const [fiscal_settings] = defineField('fiscal_settings');
  const [endereco_principal] = defineField('endereco_principal');
  const [certificado_senha] = defineField('certificado_senha');

  // =============================================
  // API Error State
  // =============================================

  const apiError = ref<string | null>(null);

  // =============================================
  // Computed States
  // =============================================

  const isDirty = computed(() => meta.value.dirty);

  const isPending = computed(() => updateMutation.isPending.value);

  const canEmitirProducao = computed(() => {
    const settings = fiscal_settings.value;
    if (!settings) return false;

    const hasCertificado =
      settings.tipo_certificado === 'ARQUIVO'
        ? !!settings.certificado_digital_path
        : !!settings.certificado_thumbprint;

    return hasCertificado && !!settings.csc_token && !!settings.csc_id;
  });

  const hasCertificado = computed(() => {
    const settings = fiscal_settings.value;
    if (!settings) return false;

    return settings.tipo_certificado === 'ARQUIVO'
      ? !!settings.certificado_digital_path
      : !!settings.certificado_thumbprint;
  });

  // =============================================
  // Watchers - Sync com API
  // =============================================

  watch(
    empresaData,
    (data) => {
      if (!data) return;
      // Populate form from API data
      resetForm({
        values: {
          ...DEFAULT_FORM_VALUES,
          ...normalizeEmpresaToForm(data),
        },
      });
    },
    { immediate: true },
  );

  // =============================================
  // Transform Functions
  // =============================================

  /**
   * Transforma dados do form para payload da API
   */
  function transformToUpdatePayload(formData: EmpresaFormData): EmpresaUpdate {
    const payload: EmpresaUpdate = {
      razao_social: formData.razao_social,
      nome_fantasia: formData.nome_fantasia,
      documento: formData.documento ? unmaskDocument(formData.documento) : undefined,
      is_cnpj: formData.is_cnpj,
      email: formData.email,
      telefone: formData.telefone ? unmaskPhone(formData.telefone) : undefined,
      celular: formData.celular ? unmaskPhone(formData.celular) : undefined,
      inscricao_estadual: formData.inscricao_estadual,
      inscricao_municipal: formData.inscricao_municipal,
      regime_tributario: formData.regime_tributario,
      cnae_principal: formData.cnae_principal,
    };

    // Transform endereco_principal -> endereco[]
    if (formData.endereco_principal) {
      payload.endereco = [
        {
          ...formData.endereco_principal,
          cep: formData.endereco_principal.cep ? unmaskCep(formData.endereco_principal.cep) : '',
          codigo_ibge: formData.endereco_principal.codigo_ibge?.replace(/[^\d]/g, ''),
        } as Endereco,
      ];
    }

    // Add fiscal settings with certificado_senha
    if (formData.fiscal_settings) {
      payload.fiscal_settings = {
        ...formData.fiscal_settings,
        certificado_senha: formData.certificado_senha ?? '',
      };
    }

    return payload;
  }

  // =============================================
  // Action Handlers
  // =============================================

  function handleLogoUpload(file: File) {
    uploadLogoMutation.mutate(file, {
      onSuccess: (updatedEmpresa) => {
        url_logo.value = updatedEmpresa.url_logo || '';
      },
    });
  }

  function handleCertUpload(file: File, senha: string) {
    // Update senha local
    certificado_senha.value = senha;

    // Upload file
    uploadCertMutation.mutate(file, {
      onSuccess: (updatedEmpresa) => {
        if (updatedEmpresa.fiscal_settings) {
          fiscal_settings.value = {
            ...fiscal_settings.value,
            certificado_digital_path: updatedEmpresa.fiscal_settings.certificado_digital_path,
            certificado_validade: updatedEmpresa.fiscal_settings.certificado_validade,
          };
        }
      },
    });
  }

  function handleTestSefaz() {
    if (!empresaId.value) return;
    testSefazMutation.mutate(empresaId.value);
  }

  function handleTestPrefeitura() {
    if (!empresaId.value) return;
    testPrefeituraMutation.mutate(empresaId.value);
  }

  // =============================================
  // Submit Handler
  // =============================================

  const onSubmit = handleSubmit(
    async (formData) => {
      apiError.value = null;

      if (!empresaId.value) {
        apiError.value = 'ID da empresa não encontrado';
        return;
      }

      const payload = transformToUpdatePayload(formData);

      updateMutation.mutate(
        { data: payload },
        {
          onError: (error: any) => {
            apiError.value = error?.response?.data?.detail || 'Erro ao salvar empresa';
          },
        },
      );
    },
    (validationErrors) => {
      console.log('[DEBUG] Validation errors:', validationErrors);
    },
  );

  // =============================================
  // Build Context
  // =============================================

  const context: EmpresaFormContext = {
    // Fields
    razao_social,
    nome_fantasia,
    documento,
    is_cnpj,
    email,
    telefone,
    celular,
    inscricao_estadual,
    inscricao_municipal,
    regime_tributario,
    cnae_principal,
    url_logo,
    fiscal_settings,
    endereco_principal,
    certificado_senha,

    // State
    errors,
    submitCount,
    values,
    apiError,
    isLoading,
    isPending,
    isDirty,

    // Computed
    canEmitirProducao,
    hasCertificado,

    // Mutations state
    isUploadingLogo: computed(() => uploadLogoMutation.isPending.value),
    isUploadingCert: computed(() => uploadCertMutation.isPending.value),
    isTestingSefaz: computed(() => testSefazMutation.isPending.value),
    isTestingPrefeitura: computed(() => testPrefeituraMutation.isPending.value),
    isLoadingCertificates: computed(() => false), // refetch is manual

    // Window Certificates
    windowsCertificates: windowsCertificates.value || [],

    // Actions
    onSubmit,
    handleLogoUpload,
    handleCertUpload,
    handleTestSefaz,
    handleTestPrefeitura,
    refetchWindowsCerts,
    resetForm: () => resetForm({ values: { ...DEFAULT_FORM_VALUES } }),
  };

  // Provide to children
  provide(EMPRESA_FORM_KEY, context);

  return context;
}

// =============================================
// Consumer Composable (Inject)
// =============================================

/**
 * Inject helper para form sections
 * Retorna o context fornecido por useEmpresaFormProvider
 *
 * @throws Error se usado fora do provider
 * @returns EmpresaFormContext
 */
export function useEmpresaForm(): EmpresaFormContext {
  const context = inject(EMPRESA_FORM_KEY);

  if (!context) {
    throw new Error(
      'useEmpresaForm must be used within a component that has called useEmpresaFormProvider',
    );
  }

  return context;
}
