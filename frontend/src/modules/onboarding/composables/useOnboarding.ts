/**
 * @fileoverview Composable principal do onboarding
 * @description Gerencia o estado global do fluxo de configuração inicial,
 * incluindo navegação entre etapas e armazenamento dos dados.
 */

import { ref, computed, reactive } from 'vue';
import type {
  OnboardingStep,
  OnboardingData,
  BusinessSegment,
  DocumentType,
} from '../types/onboarding.types';

/**
 * Estado global do onboarding (singleton)
 */
const currentStep = ref<OnboardingStep>(0);
const isSubmitting = ref(false);

const onboardingData = reactive<OnboardingData>({
  company: {
    razaoSocial: '',
    nomeFantasia: '',
    tipoDocumento: 'CNPJ',
    documento: '',
    segmento: null,
  },
  contact: {
    celular: '',
    email: '',
    telefone: '',
  },
  address: {
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
  },
});

/**
 * Configuração das etapas do onboarding
 */
const STEP_CONFIG = [
  { step: 0, title: 'Bem-vindo', subtitle: 'Vamos começar!' },
  { step: 1, title: 'Qual o segmento da sua empresa?', subtitle: 'Etapa 1 de 4 - Qual o seguimento da sua empresa?' },
  { step: 2, title: 'Dados da Empresa', subtitle: 'Etapa 2 de 4 - Dados da Empresa' },
  { step: 3, title: 'Endereço', subtitle: 'Etapa 3 de 4 - Endereço' },
  { step: 4, title: 'Confirmação', subtitle: 'Etapa 4 de 4 - Confirmação' },
] as const;

/**
 * Composable que gerencia o fluxo de onboarding
 * @returns Objeto com estados e métodos do onboarding
 */
export function useOnboarding() {
  /**
   * Computed para a configuração da etapa atual
   */
  const currentStepConfig = computed(() => STEP_CONFIG[currentStep.value]);

  /**
   * Computed para verificar se pode voltar
   */
  const canGoBack = computed(() => currentStep.value > 0);

  /**
   * Computed para verificar se é a última etapa
   */
  const isLastStep = computed(() => currentStep.value === 4);

  /**
   * Computed para o progresso (0-100)
   */
  const progress = computed(() => {
    if (currentStep.value === 0) return 0;
    return (currentStep.value / 4) * 100;
  });

  /**
   * Avança para a próxima etapa
   */
  function nextStep(): void {
    if (!isLastStep.value) {
      currentStep.value = (currentStep.value + 1) as OnboardingStep;
    }
  }

  /**
   * Volta para a etapa anterior
   */
  function previousStep(): void {
    if (canGoBack) {
      currentStep.value = (currentStep.value - 1) as OnboardingStep;
    }
  }

  /**
   * Define uma etapa específica
   */
  function goToStep(step: OnboardingStep): void {
    currentStep.value = step;
  }

  /**
   * Atualiza o segmento selecionado
   */
  function setSegment(segment: BusinessSegment): void {
    onboardingData.company.segmento = segment;
  }

  /**
   * Atualiza os dados da empresa
   */
  function updateCompanyData(data: Partial<OnboardingData['company']>): void {
    Object.assign(onboardingData.company, data);
  }

  /**
   * Atualiza os dados de contato
   */
  function updateContactData(data: Partial<OnboardingData['contact']>): void {
    Object.assign(onboardingData.contact, data);
  }

  /**
   * Atualiza os dados de endereço
   */
  function updateAddressData(data: Partial<OnboardingData['address']>): void {
    Object.assign(onboardingData.address, data);
  }

  /**
   * Atualiza o tipo de documento
   */
  function setDocumentType(type: DocumentType): void {
    onboardingData.company.tipoDocumento = type;
    onboardingData.company.documento = '';
  }

  /**
   * Reseta o estado do onboarding
   */
  function resetOnboarding(): void {
    currentStep.value = 0;
    isSubmitting.value = false;
    Object.assign(onboardingData.company, {
      razaoSocial: '',
      nomeFantasia: '',
      tipoDocumento: 'CNPJ',
      documento: '',
      segmento: null,
    });
    Object.assign(onboardingData.contact, {
      celular: '',
      email: '',
      telefone: '',
    });
    Object.assign(onboardingData.address, {
      cep: '',
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      estado: '',
    });
  }

  return {
    // Estado
    currentStep,
    onboardingData,
    isSubmitting,

    // Computed
    currentStepConfig,
    canGoBack,
    isLastStep,
    progress,

    // Métodos de navegação
    nextStep,
    previousStep,
    goToStep,

    // Métodos de atualização
    setSegment,
    setDocumentType,
    updateCompanyData,
    updateContactData,
    updateAddressData,
    resetOnboarding,
  };
}
