/**
 * @fileoverview Tipos do módulo de onboarding
 * @description Define as interfaces e tipos para o fluxo de configuração inicial
 * da empresa no sistema Start Big.
 */

import type { Component } from "vue";

/**
 * Segmentos de negócio disponíveis para seleção
 */
export type BusinessSegment =
  | 'assistencia_tecnica'
  | 'oficina_mecanica'
  | 'mercado'
  | 'marcenaria'
  | 'eletricista'
  | 'outros';

/**
 * Tipo de documento da empresa
 */
export type DocumentType = 'CNPJ' | 'CPF';

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
 * Interface para os dados da empresa
 */
export interface CompanyData {
  razaoSocial: string;
  nomeFantasia: string;
  tipoDocumento: DocumentType;
  documento: string;
  segmento: BusinessSegment | null;
}

/**
 * Interface para os dados de contato
 */
export interface ContactData {
  celular: string;
  email: string;
  telefone: string;
}

/**
 * Interface para os dados de endereço
 */
export interface AddressData {
  cep: string;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  estado: string;
}

/**
 * Interface completa dos dados de onboarding
 */
export interface OnboardingData {
  company: CompanyData;
  contact: ContactData;
  address: AddressData;
}

/**
 * Etapas do fluxo de onboarding
 */
export type OnboardingStep = 0 | 1 | 2 | 3 | 4;

/**
 * Interface para configuração de cada etapa
 */
export interface StepConfig {
  step: OnboardingStep;
  title: string;
  subtitle: string;
}

/**
 * Request para criação da empresa
 */
export interface CreateCompanyRequest {
  razao_social: string;
  nome_fantasia: string;
  tipo_documento: DocumentType;
  is_cnpj: boolean;
  documento: string;
  segmento: BusinessSegment;
  celular: string;
  email: string;
  telefone?: string;
  endereco?: AddressData[];
}

/**
 * Response da criação da empresa
 */
export interface CreateCompanyResponse {
  id: number;
  razao_social: string;
  nome_fantasia: string;
  documento: string;
  segmento: BusinessSegment;
  created_at: string;
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
