import api from '@/api/axios';
import axios from 'axios';
import type { SetupRequest, StatusResponse, ViaCepResponse } from '../types/sign-in.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Verifica se o sistema já foi inicializado (público, sem auth)
 */
export async function checkSystemStatus(): Promise<StatusResponse> {
  const { data } = await axios.get<StatusResponse>(`${API_BASE_URL}/auth/status`);
  return data;
}

/**
 * Executa o setup inicial do sistema (público, sem auth)
 * Usa axios plain para evitar interceptor 401 que redirecionaria para login.
 */
export async function setupSistema(setupData: SetupRequest): Promise<{ message: string }> {
  const { data } = await axios.post<{ message: string }>(
    `${API_BASE_URL}/auth/setup`,
    setupData,
    { withCredentials: true },
  );
  return data;
}

/**
 * Consulta endereço pelo CEP usando a API ViaCEP
 */
export async function getAddressByCep(cep: string): Promise<ViaCepResponse> {
  const { data } = await axios.get(`https://viacep.com.br/ws/${cep}/json/`);
  if (data.erro) {
    throw new Error('CEP não encontrado');
  }
  return data;
}

/**
 * Upload da logo da empresa (requer auth, chamado após setup)
 */
export async function uploadEmpresaLogo(file: File): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  await api.post('empresas/imagem', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
