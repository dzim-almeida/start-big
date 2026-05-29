/**
 * @fileoverview Serviço de onboarding
 * @description Contém as funções para comunicação com os endpoints de
 * configuração inicial da empresa e consulta de CEP.
 */

import api from '@/api/axios';
import type {
  CreateCompanyRequest,
  CreateCompanyResponse,
  ViaCepResponse,
} from '../types/onboarding.types';
import axios from 'axios';

/**
 * Consulta endereço pelo CEP usando a API ViaCEP
 * @param cep - CEP a ser consultado (apenas números)
 * @returns Promise com os dados do endereço
 */
export async function getAddressByCep(cep: string): Promise<ViaCepResponse> {
  const { data } = await axios.get(`https://viacep.com.br/ws/${cep}/json/`);
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
export async function createCompany(data: CreateCompanyRequest): Promise<CreateCompanyResponse> {
  const response = await api.post<CreateCompanyResponse>('empresas/', data);
  return response.data;
}
