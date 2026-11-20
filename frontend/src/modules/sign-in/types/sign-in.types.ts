import type { Component } from 'vue';

/**
 * Segmentos de negócio disponíveis para seleção.
 * Fonte única em `shared/constants/segmentos.ts` — reexportado aqui só para
 * não quebrar quem já importava `BusinessSegment` deste arquivo.
 */
import type { Segmento as BusinessSegment } from '@/shared/constants/segmentos';

export type { BusinessSegment };

/**
 * Tipo de pessoa do responsável
 */
export type TipoPessoa = 'PF' | 'PJ';

/**
 * Interface para os dados de um segmento de negócio
 */
export interface SegmentOption {
  id: BusinessSegment;
  label: string;
  icon: string;
  description: string;
}

export interface FeaturesOptions {
  icon: Component;
  title: string;
  description: string;
}

/**
 * Dados da loja (Passo 1)
 */
export interface LojaData {
  nomeLoja: string;
  segmento: BusinessSegment | '';
  celular: string;
  emailLoja: string;
  telefone: string;
  // Endereço
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;
}

/**
 * Dados do responsável (Passo 2)
 */
export interface ResponsavelData {
  tipoPessoa: TipoPessoa;
  nomeResponsavel: string;
  // Campos PF
  cpf: string;
  rg: string;
  genero: string;
  dataNascimento: string;
  // Campos PJ
  razaoSocial: string;
  cnpj: string;
  nomeFantasiaPJ: string;
  inscricaoEstadual: string;
  inscricaoMunicipal: string;
  regimeTributario: string;
  // Contato (ambos)
  celularResponsavel: string;
  emailResponsavel: string;
}

/**
 * Dados de acesso (Passo 3)
 */
export interface AcessoData {
  nomeUsuario: string;
  email: string;
  senha: string;
  confirmarSenha: string;
}

/**
 * Estado completo do sign-in
 */
export interface SignInData {
  loja: LojaData;
  responsavel: ResponsavelData;
  acesso: AcessoData;
}

/**
 * Etapas do fluxo de sign-in
 */
export type SignInStep = 0 | 1 | 2 | 3 | 4 | 5;

/**
 * Configuração de cada etapa
 */
export interface StepConfig {
  step: SignInStep;
  title: string;
  subtitle: string;
}

/**
 * Request para o setup inicial
 */
export interface SetupRequest {
  // Loja
  nome_loja: string;
  segmento?: string;
  celular?: string;
  email_loja?: string;
  telefone?: string;
  endereco?: {
    logradouro: string;
    numero: string;
    bairro: string;
    cidade: string;
    estado: string;
    cep: string;
    complemento?: string;
  }[];
  // Responsável
  tipo_pessoa: TipoPessoa;
  nome_responsavel: string;
  // PF
  cpf?: string;
  rg?: string;
  genero?: string;
  data_nascimento?: string;
  // PJ
  razao_social?: string;
  cnpj?: string;
  nome_fantasia_pj?: string;
  inscricao_estadual?: string;
  inscricao_municipal?: string;
  regime_tributario?: string;
  // Contato responsável
  celular_responsavel?: string;
  email_responsavel?: string;
  // Acesso
  nome_usuario: string;
  email: string;
  senha: string;
}

/**
 * Response da API ViaCEP
 */
export interface ViaCepResponse {
  cep: string;
  logradouro: string;
  complemento: string;
  bairro: string;
  localidade: string;
  uf: string;
  erro?: boolean;
}

/**
 * Backup encontrado na nuvem, mostrado depois do re-login (LIC-03 §6.2).
 * `ciclo` é a semana (data ISO); `ultimo_envio` pode não vir da nuvem.
 */
export interface BackupEncontrado {
  ciclo: string;
  ultimo_envio: string | null;
}

/** Endereço do titular, como a nuvem guarda. */
export interface EnderecoTitular {
  cep: string;
  logradouro: string;
  numero: string;
  bairro: string;
  cidade: string;
  estado: string;
}

/** Dados do titular da conta na nuvem (LIC-03 §6.6). O documento é só para LEITURA. */
export interface TitularNuvem {
  tipoPessoa: string;
  nomeOuRazao: string;
  documento: string;
  nomeFantasia?: string | null;
  telefone?: string | null;
  celular?: string | null;
  endereco?: EnderecoTitular | null;
}

/**
 * Resposta do /auth/reconnect. `backup` e `titular` só vêm quando o banco
 * ainda não tem empresa (`inicializado` = false) e podem ser null.
 */
export interface ReconnectResponse {
  success: boolean;
  inicializado: boolean;
  backup?: BackupEncontrado | null;
  titular?: TitularNuvem | null;
}

/** Resposta de POST /licenca/restaurar-backup. */
export interface RestaurarBackupResposta {
  status: 'pendente_reinicio';
  ciclo: string;
  mensagem: string;
}
