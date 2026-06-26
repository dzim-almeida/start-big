/**
 * @fileoverview Serviço de verificação de licença.
 * Usa axios puro (sem interceptor 401) pois executa antes da autenticação.
 */

import axios from 'axios';
import { getApiBaseUrl } from '@/api/backendUrl';

export interface LicencaStatusResponse {
  status: 'online_valid' | 'offline_valid';
  dias_restantes?: number;
}

export interface LicencaErroResponse {
  codigo: string;
  mensagem: string;
}

/**
 * Verifica o status da licença via GET /licenca/status.
 * Endpoint público (sem autenticação).
 */
export async function verificarLicenca(): Promise<LicencaStatusResponse> {
  const { data } = await axios.get<LicencaStatusResponse>(
    `${getApiBaseUrl()}/licenca/status`,
  );
  return data;
}
