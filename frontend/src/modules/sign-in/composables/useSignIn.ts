import { ref, computed, reactive } from 'vue';
import type { SignInStep, SignInData, LojaData, ResponsavelData, AcessoData } from '../types/sign-in.types';

/**
 * Estado global do sign-in (singleton)
 */
const currentStep = ref<SignInStep>(0);
const logoFile = ref<File | null>(null);
const logoPreview = ref<string | null>(null);

const signInData = reactive<SignInData>({
  loja: {
    nomeLoja: '',
    segmento: '',
    celular: '',
    emailLoja: '',
    telefone: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
  },
  responsavel: {
    tipoPessoa: 'PF',
    nomeResponsavel: '',
    cpf: '',
    rg: '',
    genero: '',
    dataNascimento: '',
    razaoSocial: '',
    cnpj: '',
    nomeFantasiaPJ: '',
    inscricaoEstadual: '',
    inscricaoMunicipal: '',
    regimeTributario: '',
    celularResponsavel: '',
    emailResponsavel: '',
  },
  acesso: {
    nomeUsuario: '',
    email: '',
    senha: '',
    confirmarSenha: '',
  },
});

/**
 * Configuração das etapas do sign-in
 */
const STEP_CONFIG = [
  { step: 0, title: 'Bem-vindo', subtitle: 'Vamos começar!' },
  { step: 1, title: 'Segmento', subtitle: 'Etapa 1 de 5 - Tipo de Negócio' },
  { step: 2, title: 'Dados da Loja', subtitle: 'Etapa 2 de 5 - Registro da Loja' },
  { step: 3, title: 'Dados do Responsável', subtitle: 'Etapa 3 de 5 - Responsável pelo Negócio' },
  { step: 4, title: 'Dados de Acesso', subtitle: 'Etapa 4 de 5 - Credenciais do Sistema' },
  { step: 5, title: 'Resumo', subtitle: 'Etapa 5 de 5 - Confirmação' },
] as const;

/**
 * Composable que gerencia o fluxo de sign-in
 */
export function useSignIn() {
  const currentStepConfig = computed(() => STEP_CONFIG[currentStep.value]);
  const canGoBack = computed(() => currentStep.value > 0);
  const isLastStep = computed(() => currentStep.value === 5);

  const progress = computed(() => {
    if (currentStep.value === 0) return 0;
    return (currentStep.value / 5) * 100;
  });

  function nextStep(): void {
    if (!isLastStep.value) {
      currentStep.value = (currentStep.value + 1) as SignInStep;
    }
  }

  function previousStep(): void {
    if (canGoBack.value) {
      currentStep.value = (currentStep.value - 1) as SignInStep;
    }
  }

  function goToStep(step: SignInStep): void {
    currentStep.value = step;
  }

  function updateLojaData(data: Partial<LojaData>): void {
    Object.assign(signInData.loja, data);
  }

  function updateResponsavelData(data: Partial<ResponsavelData>): void {
    Object.assign(signInData.responsavel, data);
  }

  function updateAcessoData(data: Partial<AcessoData>): void {
    Object.assign(signInData.acesso, data);
  }

  function setLogoFile(file: File | null): void {
    if (logoPreview.value) URL.revokeObjectURL(logoPreview.value);
    logoFile.value = file;
    logoPreview.value = file ? URL.createObjectURL(file) : null;
  }

  function resetSignIn(): void {
    currentStep.value = 0;

    if (logoPreview.value) URL.revokeObjectURL(logoPreview.value);
    logoFile.value = null;
    logoPreview.value = null;

    Object.assign(signInData.loja, {
      nomeLoja: '',
      segmento: '',
      celular: '',
      emailLoja: '',
      telefone: '',
      cep: '',
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      estado: '',
    });

    Object.assign(signInData.responsavel, {
      tipoPessoa: 'PF',
      nomeResponsavel: '',
      cpf: '',
      rg: '',
      genero: '',
      dataNascimento: '',
      razaoSocial: '',
      cnpj: '',
      nomeFantasiaPJ: '',
      inscricaoEstadual: '',
      inscricaoMunicipal: '',
      regimeTributario: '',
      celularResponsavel: '',
      emailResponsavel: '',
    });

    Object.assign(signInData.acesso, {
      nomeUsuario: '',
      email: '',
      senha: '',
      confirmarSenha: '',
    });
  }

  return {
    currentStep,
    signInData,
    logoFile,
    logoPreview,

    currentStepConfig,
    canGoBack,
    isLastStep,
    progress,

    nextStep,
    previousStep,
    goToStep,
    updateLojaData,
    updateResponsavelData,
    updateAcessoData,
    setLogoFile,
    resetSignIn,
  };
}
