/**
 * @fileoverview Serviço de onboarding
 * @description Contém as funções para comunicação com os endpoints de
 * configuração inicial da empresa e consulta de CEP.
 */

import api from '@/shared/libs/axios';
import type {
  CreateCompanyRequest,
  CreateCompanyResponse,
  ViaCepResponse,
} from '../types/onboarding.types';

/**
 * Consulta endereço pelo CEP usando a API ViaCEP
 * @param cep - CEP a ser consultado (apenas números)
 * @returns Promise com os dados do endereço
 */
export async function fetchAddressByCep(cep: string): Promise<ViaCepResponse> {
  const cleanCep = cep.replace(/\D/g, '');
  const response = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`);
  const data = await response.json();

  if (data.erro) {
    throw new Error('CEP não encontrado');
  }

  return data;
}

/**
 * Cria uma nova empresa no sistema
 * @param data - Dados da empresa
 * @returns Promise com os dados da empresa criada
 */
export async function createCompany(
  data: CreateCompanyRequest
): Promise<CreateCompanyResponse> {
  const response = await api.post<CreateCompanyResponse>('empresas/', data);
  return response.data;
}

/**
 * Formata um documento removendo caracteres especiais
 * @param documento - Documento formatado
 * @returns Documento apenas com números
 */
export function cleanDocument(documento: string): string {
  return documento.replace(/\D/g, '');
}

/**
 * Formata um telefone removendo caracteres especiais
 * @param telefone - Telefone formatado
 * @returns Telefone apenas com números
 */
export function cleanPhone(telefone: string): string {
  return telefone.replace(/\D/g, '');
}
