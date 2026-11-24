import { ref, computed, reactive } from 'vue';
import type {
  SignInStep,
  SignInData,
  LojaData,
  ResponsavelData,
  AcessoData,
  BackupEncontrado,
  TitularNuvem,
} from '../types/sign-in.types';

/**
 * Estado global do sign-in (singleton)
 */
const currentStep = ref<SignInStep>(0);
const logoFile = ref<File | null>(null);
const logoPreview = ref<string | null>(null);
/**
 * Em que tela do primeiro acesso estamos:
 * - choice: "Já tenho conta" ou "Começar agora";
 * - autocadastro: as etapas do setup (segmento, loja, responsável...);
 * - reconnect: o login com a conta StartBig (re-login);
 * - escolha-restauracao: "Sua licença foi encontrada" (LIC-03 §6.2, quadros 1a e 1b);
 * - restauracao-preparada: o backup foi baixado e espera reiniciar (quadro 2);
 * - confirmar-email: o cadastro novo espera a confirmação do e-mail (quadro 3a).
 */
export type SignInMode =
  | 'choice'
  | 'autocadastro'
  | 'reconnect'
  | 'escolha-restauracao'
  | 'restauracao-preparada'
  | 'confirmar-email';
const signInMode = ref<SignInMode>('choice');

/**
 * O que o re-login trouxe da nuvem (LIC-03): se há backup e os dados do
 * titular. Os dois podem ser null (sem backup, ou a nuvem não respondeu).
 */
const dadosRelogin = reactive<{ backup: BackupEncontrado | null; titular: TitularNuvem | null }>({
  backup: null,
  titular: null,
});

/** E-mail que recebeu as instruções de confirmação (quadro 3a). */
const emailConfirmacao = ref('');

/** Ciclo e mensagem da restauração preparada (quadro 2). */
const restauracaoPreparada = ref<{ ciclo: string; mensagem: string } | null>(null);

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
    if (currentStep.value === 3 && signInMode.value === 'reconnect') {
      // Pula a etapa de Acesso (4) preenchendo automaticamente o nome de usuário
      const nome = signInData.responsavel.tipoPessoa === 'PF' 
        ? signInData.responsavel.nomeResponsavel 
        : (signInData.responsavel.nomeFantasiaPJ || signInData.responsavel.razaoSocial);
      signInData.acesso.nomeUsuario = nome;
      currentStep.value = 5 as SignInStep;
    } else if (!isLastStep.value) {
      currentStep.value = (currentStep.value + 1) as SignInStep;
    }
  }

  function previousStep(): void {
    if (currentStep.value === 5 && signInMode.value === 'reconnect') {
      currentStep.value = 3 as SignInStep;
    } else if (canGoBack.value) {
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
    signInMode.value = 'choice';
    dadosRelogin.backup = null;
    dadosRelogin.titular = null;
    emailConfirmacao.value = '';
    restauracaoPreparada.value = null;

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

  /**
   * Preenche o setup com os dados do titular que vieram da nuvem (LIC-03 §6.6).
   * O documento vem preenchido e fica TRAVADO na tela (`documentoTravado`):
   * só o suporte muda o CPF/CNPJ do titular.
   */
  function aplicarTitular(titular: TitularNuvem): void {
    dadosRelogin.titular = titular;
    const ehPJ = titular.tipoPessoa === 'PJ';
    Object.assign(signInData.responsavel, {
      tipoPessoa: ehPJ ? 'PJ' : 'PF',
      // Em PF o "nome ou razão" é o nome da pessoa; em PJ, a razão social.
      nomeResponsavel: ehPJ ? signInData.responsavel.nomeResponsavel : titular.nomeOuRazao,
      razaoSocial: ehPJ ? titular.nomeOuRazao : '',
      cpf: ehPJ ? '' : titular.documento,
      cnpj: ehPJ ? titular.documento : '',
      nomeFantasiaPJ: ehPJ ? titular.nomeFantasia ?? '' : '',
      celularResponsavel: titular.celular ?? signInData.responsavel.celularResponsavel,
      // Mesmo caso do e-mail da loja: o da conta é o ponto de partida.
      emailResponsavel: signInData.responsavel.emailResponsavel || signInData.acesso.email,
    });
    Object.assign(signInData.loja, {
      nomeLoja: titular.nomeFantasia || signInData.loja.nomeLoja,
      // A nuvem não guarda um e-mail da loja: o da conta (o que acabou de
      // entrar) é o ponto de partida, e a pessoa pode trocar.
      emailLoja: signInData.loja.emailLoja || signInData.acesso.email,
      celular: titular.celular ?? signInData.loja.celular,
      telefone: titular.telefone ?? signInData.loja.telefone,
      ...(titular.endereco && {
        cep: titular.endereco.cep,
        logradouro: titular.endereco.logradouro,
        numero: titular.endereco.numero,
        bairro: titular.endereco.bairro,
        cidade: titular.endereco.cidade,
        estado: titular.endereco.estado,
      }),
    });
  }

  /** O documento veio da nuvem? Então a tela não deixa editar (CT-14). */
  const documentoTravado = computed(() => dadosRelogin.titular !== null);

  return {
    dadosRelogin,
    emailConfirmacao,
    restauracaoPreparada,
    documentoTravado,
    aplicarTitular,
    signInMode,
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
